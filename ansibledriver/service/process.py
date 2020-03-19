import json
import logging
import time
import os
import sys
import multiprocessing
import copy
import traceback
import threading
from signal import signal, getsignal, SIGINT, SIGTERM, SIGQUIT, SIGCHLD, SIG_IGN, SIG_DFL
from multiprocessing import Process, RawValue, Lock, Pipe, active_children
from multiprocessing.pool import Pool
from collections import namedtuple
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ignition.service.lifecycle import LifecycleDriverCapability
from ignition.service.framework import Service, Capability, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.logging import logging_context
from ignition.service.requestqueue import RequestHandler

logger = logging.getLogger(__name__)

class AnsibleProcessorCapability(Capability):

    @interface
    def shutdown(self):
        pass

class ProcessProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('process')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.process_pool_size = 2
        self.use_process_pool = True

class AnsibleProcessorService(Service, AnsibleProcessorCapability):
    def __init__(self, configuration, ansible_client, **kwargs):
        self.active = False

        if 'messaging_service' not in kwargs:
            raise ValueError('messaging_service argument not provided')
        if 'request_queue_service' not in kwargs:
            raise ValueError('request_queue_service argument not provided')

        self.messaging_service = kwargs.get('messaging_service')
        self.process_properties = configuration.property_groups.get_property_group(ProcessProperties)

        # lifecycle requests are placed on this queue
        self.request_queue_service = kwargs.get('request_queue_service')

        self.ansible_client = ansible_client

        # gracefully deal with SIGINT
        signal(SIGINT, self.sigint_handler)
        self.sigchld_handler = getsignal(SIGCHLD)

        self.active = True

        # a pool of (Ansible) processes reads from the request_queue
        # we don't using a multiprocessing.Pool here because it uses daemon processes which cannot
        # create sub-processes (and Ansible requires this)
        self.pool = [None] * self.process_properties.process_pool_size
        for i in range(self.process_properties.process_pool_size):
          self.pool[i] = AnsibleProcess(self, 'AnsiblePoolProcess{0}'.format(i), self.request_queue_service, self.ansible_client, self.messaging_service, self.sigchld_handler)
          self.pool[i].daemon = False
          self.pool[i].start()

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


## Ansible Process Pools

class AnsibleProcess(Process):

    def __init__(self, ansible_processor, name, request_queue_service, ansible_client, messaging_service, sigchld_handler, **kwargs):
      super(AnsibleProcess, self).__init__(daemon=False)
      self.name = name
      self.ansible_processor = ansible_processor
      self.request_queue_service = request_queue_service
      self.messaging_service = messaging_service
      self.ansible_client = ansible_client
      self.sigchld_handler = sigchld_handler
      self.kwargs = kwargs
      self.request_queue = request_queue_service.get_lifecycle_request_queue(name, AnsibleRequestHandler(messaging_service, ansible_client))
      logger.debug('Created worker process: {0} {1}'.format(name, self.request_queue))

    def sigint_handler(self, sig, frame):
      logger.debug('caught sigint in Ansible Process Worker {0}'.format(self.name))
      exit(0)

    def run(self):
      try:
        if threading.main_thread():
          signal(SIGINT, self.sigint_handler)
          # make sure Ansible processes are acknowledged to avoid zombie processes
          signal(SIGCHLD, self.sigchld_handler)

        logger.debug('Initialised ansible worker process {0}'.format(self.name))
        # continually read from the request queue and process Ansible lifecycle requests
        while self.ansible_processor.active == True:
          # note: request_queue handles all exceptions
          self.request_queue.process_request()

      finally:
        self.request_queue.close()


"""
Handler for Ansible driver request queue messages/requests.
"""
class AnsibleRequestHandler(RequestHandler):
    def __init__(self, messaging_service, ansible_client):
      super(AnsibleRequestHandler, self).__init__()
      self.messaging_service = messaging_service
      self.ansible_client = ansible_client

    def handle_request(self, request):
      try:
        if request is not None:
          if request.get('logging_context', None) is not None:
              logging_context.set_from_dict(request['logging_context'])

          if 'request_id' not in request:
            self.messaging_service.send_lifecycle_execution(LifecycleExecution(None, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a request_id"), {}))
          if 'lifecycle_name' not in request:
            self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_name"), {}))
          if 'lifecycle_path' not in request:
            self.messaging_service.send_lifecycle_execution(LifecycleExecution(request['request_id'], STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_path"), {}))
 
          # run the playbook and send the response to the response queue
          logger.debug('Ansible worker running request {0}'.format(request))
          result = self.ansible_client.run_lifecycle_playbook(request)
          if result is not None:
            logger.debug('Ansible worker finished for request {0}: {1}'.format(request, result))
            self.messaging_service.send_lifecycle_execution(result)
          else:
            logger.warn("Empty response from Ansible worker for request {0}".format(request))
        else:
          logger.warn('Null lifecycle request from request queue')
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


