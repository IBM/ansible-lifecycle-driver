import json
import logging
import time
import os
import sys
import multiprocessing
import copy
import traceback
import threading
from signal import signal, SIGINT, SIGTERM, SIGQUIT, SIGCHLD, SIG_IGN, SIG_DFL
from multiprocessing import Process, RawValue, Lock, Pipe, active_children
from multiprocessing.pool import Pool
from collections import namedtuple
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ignition.service.lifecycle import LifecycleDriverCapability
from ignition.service.framework import Service, Capability, interface
from ansibledriver.service.queue import SHUTDOWN_MESSAGE
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.logging import logging_context

logger = logging.getLogger(__name__)

class AnsibleProcessorCapability(Capability):

    @interface
    def queue_status(self):
        pass

class ProcessProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('process')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.process_pool_size = 2
        self.max_concurrent_ansible_processes = 10
        self.max_queue_size = 100
        self.use_process_pool = True
        self.is_threaded = False

class AnsibleProcessorService(Service, AnsibleProcessorCapability):
    def __init__(self, configuration, request_queue, response_queue, ansible_client, **kwargs):
        if 'messaging_service' not in kwargs:
            raise ValueError('messaging_service argument not provided')
        self.active = False
        self.messaging_service = kwargs.get('messaging_service')
        self.queue_thread = None
        self.process_properties = configuration.property_groups.get_property_group(ProcessProperties)

        # lifecycle requests are placed on this queue
        self.request_queue = request_queue

        self.response_queue = response_queue
        self.ansible_client = ansible_client
        self.counter = Counter()

        # gracefully deal with SIGINT
        signal(SIGINT, self.sigint_handler)

        self.active = True

        if self.process_properties.use_process_pool:
          # a pool of (Ansible) processes reads from the request_queue
          # we don't using a multiprocessing.Pool here because it uses daemon processes which cannot
          # create sub-processes (and Ansible requires this)
          self.pool = [None] * self.process_properties.process_pool_size
          for i in range(self.process_properties.process_pool_size):
            self.pool[i] = AnsibleProcess(self, 'AnsiblePoolProcess{0}'.format(i), self.request_queue, self.ansible_client, self.response_queue)
            self.pool[i].daemon = False
            self.pool[i].start()
        else:
          self.queue_thread = QueueThread(self, self.ansible_client, self.send_pipe, self.process_properties, self.request_queue, self.counter)

        # Ansible process reponse thread listens for messages on the recv_pipe sends the response to Kafka
        self.responses_thread = ResponsesThread(self, self.response_queue)

        self.responses_thread.start()
        if self.queue_thread is not None:
          self.queue_thread.start()

    def ansible_process_done(self):
      self.counter.decrement()

    # remove deployment location properties from the request (to prevent logging sensitive information)
    def request_without_dl_properties(self, request):
      request_copy = copy.deepcopy(request)
      if request_copy.get('deployment_location', None) is not None:
        if request_copy['deployment_location'].get('properties', None) is not None:
          request_copy['deployment_location']['properties'] = '***obfuscated properties***'
      return request_copy

    def run_lifecycle(self, request, keep_scripts=False):
      accepted = False
      try:
        if 'request_id' not in request:
          raise ValueError('Request must have a request_id')
        if 'lifecycle_name' not in request:
          raise ValueError('Request must have a lifecycle_name')
        if 'lifecycle_path' not in request:
          raise ValueError('Request must have a lifecycle_path')
        request['keep_scripts'] = keep_scripts

        # add logging context to request
        request['logging_context'] = logging_context.get_all()

        logger.debug('request_queue.size {0} max_queue_size {1}'.format(self.request_queue.size(), self.process_properties.max_queue_size))
        if self.active == True:
          if self.request_queue.size() >= self.process_properties.max_queue_size:
            self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INSUFFICIENT_CAPACITY, "Request cannot be handled, driver is overloaded"), {}))
          else:
            logger.debug('Adding request {0} to queue'.format(self.request_without_dl_properties(request)))
            self.request_queue.put(request)
            accepted = True
        else:
          # inactive, just return a standard response
          self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INSUFFICIENT_CAPACITY, "Driver is inactive"), {}))
      finally:
        if not accepted and not keep_scripts and 'lifecycle_path' in request:
          try:
            logger.debug('Attempting to remove lifecycle scripts at {0}'.format(request['lifecycle_path'].root_path))
            request['lifecycle_path'].remove_all()
          except Exception as e:
            logger.exception('Encountered an error whilst trying to clear out lifecycle scripts directory {0}: {1}'.format(request['lifecycle_path'].root_path, str(e)))

    def queue_status(self):
      return self.request_queue.queue_status()

    def ansible_process_worker(self, process_name, request_queue, send_pipe):
      logger.info('{0} initialised'.format(process_name))
      # make sure Ansible processes are acknowledged to avoid zombie processes
      signal(SIGCHLD, SIG_IGN)
      while(True):
        try:
          request = request_queue.next()
          if request is not None:
            send_pipe.send(self.ansible_client.run_lifecycle_playbook(request))

            logger.debug('Ansible worker finished for request {0}'.format(request))
        except Exception as e:
          logger.error('Unexpected exception {0}'.format(e))
          traceback.print_exc(file=sys.stderr)
          # don't want the worker to die without knowing the cause, so catch all exceptions
          if request is not None:
            send_pipe.send(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))

    def sigint_handler(self, sig, frame):
      logger.debug('sigint_handler')
      self.shutdown()
      exit(0)

    def shutdown(self):
      if self.active:
        logger.debug('shutdown')

        self.active = False

        logger.info('Shutting down request queue')
        print('Shutting down request queue')
        self.request_queue.shutdown()
        logger.info('Shutting down response queue')
        print('Shutting down response queue')
        self.response_queue.shutdown()

        print('Shutting down process pool')
        if self.process_properties.use_process_pool:
          logger.debug("Terminating Ansible processes")
          print("Terminating Ansible processes")
          for p in self.pool:
            if p is not None and p.is_alive():
              logger.debug("Terminating Ansible Driver process {0}".format(p.name))
              p.terminate()

    def to_lifecycle_execution(self, json):
      if json.get('failure_details', None) is not None:
        failure_details = FailureDetails(json['failure_details']['failure_code'], json['failure_details']['description'])
      else:
        failure_details = None
      return LifecycleExecution(json['request_id'], json['status'], failure_details, json['outputs'])


## Ansible Process Pools

class AnsibleProcess(Process):

    def __init__(self, ansible_processor, name, request_queue, ansible_client, response_queue, **kwargs):
      super(AnsibleProcess, self).__init__(daemon=False)
      self.name = name
      self.ansible_processor = ansible_processor
      self.request_queue = request_queue
      self.ansible_client = ansible_client
      self.response_queue = response_queue
      self.kwargs = kwargs

      logger.debug('Created worker process: {0}'.format(name))

    def sigint_handler(self, sig, frame):
      logger.debug('caught sigint in Ansible Process Worker {0}'.format(self.name))
      exit(0)

    def run(self):
      try:
        signal(SIGINT, self.sigint_handler)
        
        logger.info('Initialised worker process {0}'.format(self.name))
        while self.ansible_processor.active:
          request = self.request_queue.next()
          try:
            if request == SHUTDOWN_MESSAGE:
              break
            else:
              # clean up zombie processes (Ansible can leave these behind)
              for p in active_children():
                logger.debug("removed zombie process {0}".format(p.name))
              if request is not None:
                if request.get('logging_context', None) is not None:
                  logging_context.set_from_dict(request['logging_context'])

                try:
                  print('Ansible worker running request {0}'.format(request))
                  logger.debug('Ansible worker running request {0}'.format(request))
                  resp = self.ansible_client.run_lifecycle_playbook(request)
                  if resp is not None:
                    self.response_queue.put(resp)
                  else:
                    logger.warn("Empty response from Ansible worker for request {0}".format(request))
                finally:
                  logging_context.clear()
          except Exception as e:
            logger.exception('Unexpected exception {0}'.format(e))
            traceback.print_exc(file=sys.stderr)
            # don't want the worker to die without knowing the cause, so catch all exceptions
            if request is not None:
              self.response_queue.put(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
          finally:
            self.request_queue.task_done()

            # clean up zombie processes (Ansible can leave these behind)
            for p in active_children():
              logger.debug("removed zombie process {0}".format(p.name))

        logger.debug('Worker process {0} finished'.format(self.name))
      except Exception as e:
        logger.exception('Unexpected exception {0}'.format(e))
        traceback.print_exc(file=sys.stderr)


## Threaded Ansible worker

class QueueThread(threading.Thread):

    def __init__(self, ansible_processor, ansible_client, send_pipe, process_properties, request_queue, counter):
      self.ansible_processor = ansible_processor
      self.ansible_client = ansible_client
      self.send_pipe = send_pipe
      self.process_properties = process_properties
      self.request_queue = request_queue
      self.counter = counter
      super().__init__(daemon = True)

    def run(self):
      while self.ansible_processor.active:
        try:
          request = self.request_queue.next()
          if request is not None:
            if request == SHUTDOWN_MESSAGE:
              self.request_queue.task_done()
              break
            elif self.counter.value() < self.process_properties.max_concurrent_ansible_processes:
              try:
                logger.debug('Got request from queue: {0}'.format(request))
                if(request == SHUTDOWN_MESSAGE):
                  self.request_queue.task_done()
                  break
                else:
                  self.counter.increment()

                  if self.process_properties.is_threaded:
                    worker = AnsibleWorkerThread(self.ansible_client, request, self.send_pipe)
                    worker.start()
                    logger.debug('Request processing started for request {0} with thread {1}'.format(request, worker.ident))
                  else:
                    logger.debug('Creating worker process')
                    worker = AnsibleWorkerProcess(self.ansible_client, request, self.send_pipe)
                    logger.debug('Created worker process')
                    worker.start()
                    logger.debug('Request processing started for request {0} with pid {1}'.format(request, worker.pid))
              finally:
                self.request_queue.task_done()
            else:
              self.request_queue.task_done()
              logger.debug('Max processes reached, re-queuing request {0}'.format(request))
              # this may increase the queue above the requested bounds but the increase will be bounded
              # by the max processes setting and not by the number of requests coming in
              # TODO will this put to back of queue?
              self.request_queue.put(request)
        except Exception as e:
          traceback.print_exc(file=sys.stdout)
          logger.error('Unexpected exception {0}'.format(e))

class AnsibleWorkerThread(threading.Thread):

    def __init__(self, ansible_client, request, send_pipe):
      self.ansible_client = ansible_client
      self.request = request
      self.send_pipe = send_pipe
      super().__init__(daemon = True)

    def run(self):
      try:
        if self.request is not None:
          if self.request.get('logging_context', None) is not None:
            logging_context.set_from_dict(self.request['logging_context'])

          resp = self.ansible_client.run_lifecycle_playbook(self.request)
          if resp is not None:
            logger.debug('Ansible worker finished for request {0} response {1}'.format(self.request, resp))
            self.send_pipe.send(resp)
          else:
            logger.warn("Empty response from Ansible worker for request {0}".format(self.request))
        else:
          pass
          # TODO
      except Exception as e:
        logger.error('Unexpected exception {0}'.format(e))
        traceback.print_exc(file=sys.stderr)
        # don't want the worker to die without knowing the cause, so catch all exceptions
        if self.request is not None:
          self.send_pipe.send(LifecycleExecution(self.request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
      finally:
        logging_context.clear()


class AnsibleWorkerProcess(Process):

    def __init__(self, ansible_client, request, send_pipe):
      self.ansible_client = ansible_client
      self.request = request
      self.send_pipe = send_pipe
      super().__init__(daemon = False)

    def run(self):
      try:
        if self.request is not None:
          if self.request.get('logging_context', None) is not None:
            logging_context.set_from_dict(self.request['logging_context'])

          resp = self.ansible_client.run_lifecycle_playbook(self.request)
          if resp is not None:
            logger.debug('Ansible worker finished for request {0} response {1}'.format(self.request, resp))
            self.send_pipe.send(resp)
          else:
            logger.warn("Empty response from Ansible worker for request {0}".format(self.request))
        else:
          pass
      except Exception as e:
        logger.error('Unexpected exception {0}'.format(e))
        traceback.print_exc(file=sys.stderr)
        # don't want the worker to die without knowing the cause, so catch all exceptions
        if self.request is not None:
          self.send_pipe.send(LifecycleExecution(self.request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
      finally:
        logging_context.clear()


## Ansible response handling thread

class ResponsesThread(threading.Thread):

    def __init__(self, ansible_processor_service, response_queue):
      self.ansible_processor_service = ansible_processor_service
      self.response_queue = response_queue
      super().__init__(daemon = True)

    def run(self):
      while self.ansible_processor_service.active:
        try:
          result = self.response_queue.next()
          self.ansible_processor_service.ansible_process_done()

          if result is not None:
            logger.debug('Responses thread received {0}'.format(result))
            self.ansible_processor_service.messaging_service.send_lifecycle_execution(result)
          else:
            # nothing to do
            pass
        except EOFError as error:
          # nothing to do - ignore
          pass
        finally:
          self.response_queue.task_done()


class Counter(object):
    def __init__(self, value=0):
        # RawValue because we don't need it to create a Lock:
        self.val = RawValue('i', value)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def decrement(self):
        with self.lock:
            self.val.value -= 1

    def value(self):
        with self.lock:
            return self.val.value
