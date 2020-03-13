import unittest
import uuid
import json
import logging
import sys
import signal
import threading
import tempfile
import time
from unittest.mock import call, patch, MagicMock, ANY, DEFAULT
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ansibledriver.service.cache import CacheProperties
from ansibledriver.service.process import AnsibleProcessorService, ProcessProperties, AnsibleProcess, AnsibleRequestHandler
from ansibledriver.service.ansible import AnsibleProperties
from ignition.utils.file import DirectoryTree
from ignition.utils.propvaluemap import PropValueMap
from testfixtures import compare

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

def sleep(request_id, lifecycle_execution, *args, **kwargs):
  logger.info('sleeping for request {0}...'.format(request_id))
  time.sleep(4)
  return lifecycle_execution

class LifecycleExecutionMatcher:
  def __init__(self, expected):
    self.expected = expected

  def compare(self, other):
    if not type(self.expected) == type(other):
      return False
    if other.status != self.expected.status:
      return False
    if other.request_id != self.expected.request_id:
      return False
    if len(self.expected.outputs.items() - other.outputs.items()) > 0:
      return False
    if self.expected.failure_details is not None:
        if other.failure_details is None:
            return False
        if other.failure_details.failure_code != self.expected.failure_details.failure_code:
          return False
        if other.failure_details.description != self.expected.failure_details.description:
          return False

    return True

  def __str__(self):
    return 'expected: {0.expected}'.format(self)

  # "other" is the actual argument, to be compared against self.expected
  def __eq__(self, other):
    return self.compare(other)

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

    def check_response(self, mock_ansible_client, lifecycle_execution):
      for i in range(50):
        if mock_ansible_client.run_lifecycle_playbook.call_count > 0:
          mock_ansible_client.run_lifecycle_playbook.assert_called_once()

        if self.mock_messaging_service.send_lifecycle_execution.call_count > 0:
          name, args, kwargs = self.mock_messaging_service.send_lifecycle_execution.mock_calls[0]
          print('args=' + str(len(args)))
          compare(args[0], lifecycle_execution)
          break
        else:
          logger.info('check_response, iteration {0}...'.format(i))
          time.sleep(1)
      else:
        self.fail('Timeout waiting for response')

    def check_response_only(self, lifecycle_execution):
      print("check_response_only {}".format(lifecycle_execution))
      for i in range(50):
        if self.mock_messaging_service.send_lifecycle_execution.call_count > 0:
          name, args, kwargs = self.mock_messaging_service.send_lifecycle_execution.mock_calls[0]
          print('args={}'.format(args[0]))
          compare(args[0], lifecycle_execution)
          break
        else:
          logger.info('check_response, iteration {0}...'.format(i))
          time.sleep(1)
      else:
        self.fail('Timeout waiting for response')

    # def check_response(self, lifecycle_execution):
    #   for i in range(50):
    #     call_count = self.mock_messaging_service.send_lifecycle_execution.call_count
    #     if call_count > 0:
    #       self.mock_messaging_service.send_lifecycle_execution.assert_called_with(LifecycleExecutionMatcher(lifecycle_execution))
    #       break
    #     else:
    #       logger.info('check_responses, iteration {0}...'.format(i))
    #       time.sleep(1)
    #   else:
    #     self.fail('Timeout waiting for response')

    def check_responses(self, lifecycle_executions):
      # loop until there are at least two calls to the Kafka messaging, and then check that the messages are what we expect
      for i in range(50):
        call_count = self.mock_messaging_service.send_lifecycle_execution.call_count
        if call_count >= len(lifecycle_executions):
          assert self.mock_messaging_service.send_lifecycle_execution.call_args_list == list(map(lambda lifecycle_execution: call(LifecycleExecutionMatcher(lifecycle_execution)), lifecycle_executions))
          break
        else:
          logger.info('check_responses, iteration {0}...'.format(i))
          time.sleep(1)
      else:
        self.fail('Timeout waiting for response')

    def test_handles_empty_request(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        messaging_service = MagicMock()
        ansible_client = MagicMock()
        handler = AnsibleRequestHandler(messaging_service, ansible_client)

        self.assertTrue(handler.handle(None))

    def test_run_lifecycle_missing_request_id(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        self.assertTrue(handler.handle({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': PropValueMap({
          })
        }))
        self.check_response_only(LifecycleExecution(None, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a request_id"), {}))

    def test_run_lifecycle_missing_lifecycle_name(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        self.assertTrue(handler.handle({
          'request_id': request_id,
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': PropValueMap({
          })
        }))
        self.check_response_only(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_name"), {}))

    def test_run_lifecycle_missing_lifecycle_path(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex

        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)
        self.assertTrue(handler.handle({
          'request_id': request_id,
          'lifecycle_name': 'install',
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          }
        }))
        self.check_response_only(LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Request must have a lifecycle_path"), {}))

    def test_run_lifecycle(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id = uuid.uuid4().hex
        handler = AnsibleRequestHandler(self.mock_messaging_service, self.mock_ansible_client)

        self.mock_ansible_client.run_lifecycle_playbook.return_value = LifecycleExecution(request_id, STATUS_COMPLETE, None, {
          'prop1': 'output__value1'
        })

        self.assertTrue(handler.handle({
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
        }))

        self.check_response_only(LifecycleExecution(request_id, STATUS_COMPLETE, None, {
          'prop1': 'output__value1'
        }))

    # @patch("ansibledriver.service.ansible.AnsibleClient")
    # def test_run_lifecycle(self, mock_ansible_client):
    def test_ansible_process(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        name = "Test"
        request_id = uuid.uuid4().hex
        mock_ansible_processor = MagicMock()
        mock_ansible_processor.active = True
        mock_request_queue = MagicMock()
        mock_request_queue_service = MagicMock()
        mock_request_queue_service.get_lifecycle_request_queue.return_value = mock_request_queue
        mock_ansible_client = MagicMock()
        mock_messaging_service = MagicMock()
        sigchld_handler = signal.SIG_IGN
        ansible_process = AnsibleProcess(mock_ansible_processor, name, mock_request_queue_service, mock_ansible_client, mock_messaging_service, sigchld_handler)

        ansible_process.start()

        logger.info("mock_request_queue = {}".format(mock_request_queue))
        for i in range(50):
          logger.info("mock_request_queue.process_request.call_count = {}".format(mock_request_queue.process_request.call_count))
          if mock_request_queue.process_request.call_count > 0:
            mock_request_queue.process_request.assert_called_once()
          else:
            logger.info('check_response, iteration {0}...'.format(i))
            time.sleep(1)
        else:
          self.fail('Timeout waiting for response')
