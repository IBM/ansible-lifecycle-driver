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
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.logging import logging_context
from ansibledriver.service.queue import SHUTDOWN_MESSAGE

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
    def __init__(self, configuration, ansible_client, **kwargs):
        if 'messaging_service' not in kwargs:
            raise ValueError('messaging_service argument not provided')
        if 'request_queue_service' not in kwargs:
            raise ValueError('request_queue_service argument not provided')

        self.active = False

        self.messaging_service = kwargs.get('messaging_service')
        self.process_properties = configuration.property_groups.get_property_group(ProcessProperties)

        # lifecycle requests are placed on this queue
        self.request_queue_service = kwargs.get('request_queue_service')

        self.ansible_client = ansible_client
        self.counter = Counter()

        # gracefully deal with SIGINT
        signal(SIGINT, self.sigint_handler)

        # a pool of (Ansible) processes reads from the request_queue
        # we don't using a multiprocessing.Pool here because it uses daemon processes which cannot
        # create sub-processes (and Ansible requires this)
        self.pool = [None] * self.process_properties.process_pool_size
        for i in range(self.process_properties.process_pool_size):
          self.pool[i] = AnsibleProcess(self, 'AnsiblePoolProcess{0}'.format(i), self.request_queue_service, self.ansible_client, self.messaging_service)
          self.pool[i].daemon = False

        self.active = True

        for i in range(self.process_properties.process_pool_size):
          self.pool[i].start()

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
          self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INSUFFICIENT_CAPACITY, "Request cannot be handled, driver is overloaded"), {}))
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

    def sigint_handler(self, sig, frame):
      logger.debug('sigint_handler')
      self.shutdown()
      exit(0)

    def shutdown(self):
      logger.info('Shutting down...')

      if self.active:
        self.active = False

        if self.request_queue_service is not None:
          self.request_queue_service.close()

        logger.debug('Shutting down process pool')
        if self.process_properties.use_process_pool:
          logger.debug("Terminating Ansible processes")
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

    def __init__(self, ansible_processor, name, request_queue_service, ansible_client, messaging_service, **kwargs):
      super(AnsibleProcess, self).__init__(daemon=False)
      self.name = name
      self.ansible_processor = ansible_processor
      self.request_queue_service = request_queue_service
      self.messaging_service = messaging_service
      self.ansible_client = ansible_client
      self.kwargs = kwargs
      self.request_queue = request_queue_service.get_lifecycle_request_queue(name)

      logger.debug('Created worker process: {0}'.format(name))

    def sigint_handler(self, sig, frame):
      logger.debug('caught sigint in Ansible Process Worker {0}'.format(self.name))
      exit(0)

    def run(self):
      try:
        signal(SIGINT, self.sigint_handler)

        logger.info('Initialised worker process {0}'.format(self.name))

        def process_lifecycle_request(request):
          try:
            if request is not None:
              if request.get('logging_context', None) is not None:
                  logging_context.set_from_dict(request['logging_context'])

              logger.info('Ansible worker running request {0}'.format(request))

              # run the playbook and send the response to the pipe
              result = self.ansible_client.run_lifecycle_playbook(request)
              if result is not None:
                self.messaging_service.send_lifecycle_execution(result)
              else:
                logger.warn("Empty response from Ansible worker for request {0}".format(request))

              logger.info('Ansible worker finished for request {0}'.format(request))
            else:
              logger.warn('Null lifecycle request from queue')
          except Exception as e:
            logger.error('Unexpected exception {0}'.format(e))
            traceback.print_exc(file=sys.stderr)
            # don't want the worker to die without knowing the cause, so catch all exceptions
            if request is not None:
              self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {}))
          finally:
            # clean up zombie processes (Ansible can leave these behind)
            for p in active_children():
              logger.debug("removed zombie process {0}".format(p.name))

        # make sure Ansible processes are acknowledged to avoid zombie processes
        signal(SIGCHLD, SIG_IGN)

        # continually read from the request queue and process Ansible lifecycle requests
        while(True):
          self.request_queue.process_lifecycle_request(process_lifecycle_request)

      finally:
        self.request_queue.close()


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
