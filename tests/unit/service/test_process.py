import unittest
import uuid
import json
import logging
import sys
import signal
import os
import threading
import multiprocessing
import tempfile
import time
from unittest.mock import call, patch, MagicMock, ANY, DEFAULT
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ignition.utils.file import DirectoryTree
from ignition.utils.propvaluemap import PropValueMap
from ignition.service.requestqueue import KafkaRequestQueueHandler
from ansibledriver.service.process import AnsibleProcessorService, ProcessProperties, AnsibleProcess, AnsibleRequestHandler
from ansibledriver.service.ansible import AnsibleProperties
from testfixtures import compare

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

# PickableMock is needed to be able to make MagicMocks with multiprocessing queues pickling
# see https://github.com/testing-cabal/mock/issues/139#issuecomment-122128815
class PickableMock(MagicMock):
    def __reduce__(self):
        return (MagicMock, ())

class TestProcess(unittest.TestCase):

    def setUp(self):
        self.tmp_workspace = tempfile.mkdtemp()
        self.mock_messaging_service = MagicMock()
        self.mock_ansible_client = MagicMock()
        property_groups = PropertyGroups()
        property_groups.add_property_group(AnsibleProperties())
        process_props = ProcessProperties()
        process_props.use_pool = False
        property_groups.add_property_group(process_props)
        self.configuration = BootstrapApplicationConfiguration(app_name='test', property_sources=[], property_groups=property_groups, service_configurators=[], api_configurators=[], api_error_converter=None)
        self.ansible_processor = None

    def build_processor(self, ansible_client, configuration=None):
      if configuration is None:
        configuration = self.configuration
      self.ansible_processor = AnsibleProcessorService(configuration, self.request_queue, self.response_queue, ansible_client, messaging_service=self.mock_messaging_service)

    def tearDown(self):
      if self.ansible_processor is not None:
        self.ansible_processor.shutdown()

    def assertLifecycleExecutionEqual(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertEqual(resp.failure_details.description, expected_resp.failure_details.description)

    def check_response_only(self, lifecycle_execution):
      for i in range(50):
        if self.mock_messaging_service.send_lifecycle_execution.call_count > 0:
          name, args, kwargs = self.mock_messaging_service.send_lifecycle_execution.mock_calls[0]
          compare(args[0], lifecycle_execution)
          break
        else:
          logger.info('check_response, iteration {0}...'.format(i))
          time.sleep(1)
      else:
        self.fail('Timeout waiting for response')

    def test_handles_empty_request(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        messaging_service = MagicMock()
        ansible_client = MagicMock()
        handler = AnsibleRequestHandler(messaging_service, ansible_client)

        handler.handle_request(None)

    def test_run_lifecycle_missing_request_id(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        handler.handle_request({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': PropValueMap({
          })
        })
        self.check_response_only(LifecycleExecution(None, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a request_id"), {}))

    def test_run_lifecycle_missing_lifecycle_name(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        handler.handle_request({
          'request_id': request_id,
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': PropValueMap({
          })
        })
        self.check_response_only(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_name"), {}))

    def test_run_lifecycle_missing_lifecycle_path(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        handler.handle_request({
          'request_id': request_id,
          'lifecycle_name': 'install',
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          }
        })
        self.check_response_only(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_path"), {}))

    def test_run_lifecycle(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex
        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)

        self.mock_ansible_client.run_lifecycle_playbook.return_value = LifecycleExecution(request_id, STATUS_COMPLETE, None, {
          'prop1': 'output__value1'
        })

        handler.handle_request({
          'lifecycle_name': 'Install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
            'properties': {
              'testPropA': 'A'
            }
          },
          'request_id': request_id
        })

        self.check_response_only(LifecycleExecution(request_id, STATUS_COMPLETE, None, {
          'prop1': 'output__value1'
        }))

    def test_ansible_process(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        r, w = multiprocessing.Pipe(False)

        name = "Test"
        request_id = uuid.uuid4().hex
        request_queue = TestKafkaRequestQueueHandler(w)
        sigchld_handler = signal.SIG_IGN
        shutdown_event = multiprocessing.Event()
        ansible_process = AnsibleProcess(name, request_queue, sigchld_handler, shutdown_event)
        ansible_process.start()

        # close write end of pipe in parent
        w.close()

        for i in range(5):
          if r.poll():
            actual = r.recv()
            expected = json.dumps({
              "request_id": "123"
            }).encode()
            self.assertEqual(actual, expected)
            shutdown_event.set()
            break
          else:
            time.sleep(1)
        else:
          shutdown_event.set()
          self.fail('Timeout waiting for response')

        ansible_process.join()


class TestKafkaRequestQueueHandler(KafkaRequestQueueHandler):
    def __init__(self, pipeout):
      self.pipeout = pipeout
      self.closed = False

    def process_request(self):
      self.pipeout.send(json.dumps({
        "request_id": "123"
      }).encode())
      time.sleep(1)

    def close(self):
      self.closed = True
