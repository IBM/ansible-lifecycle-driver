import unittest
import uuid
import json
import logging
import sys
import tempfile
import time
from unittest.mock import call, patch, MagicMock, ANY, DEFAULT
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ansibledriver.service.cache import CacheProperties
from ansibledriver.service.queue import RequestQueue, ResponseQueue
from ansibledriver.service.process import AnsibleProcessorService, ProcessProperties
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
        self.request_queue = RequestQueue()
        self.response_queue = ResponseQueue()
        self.mock_messaging_service = PickableMock()
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

    def test_run_lifecycle_invalid_request(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        self.build_processor(PickableMock())

        with self.assertRaises(ValueError) as context:
          self.ansible_processor.run_lifecycle({
            'lifecycle_name': 'install',
            'lifecycle_path': DirectoryTree(self.tmp_workspace),
            'system_properties': PropValueMap({
            }),
            'properties': PropValueMap({
            }),
            'deployment_location': PropValueMap({
            })
          })
        self.assertEqual(str(context.exception), 'Request must have a request_id')

        with self.assertRaises(ValueError) as context:
          self.ansible_processor.run_lifecycle({
            'request_id': uuid.uuid4().hex,
            'lifecycle_path': DirectoryTree(self.tmp_workspace),
            'system_properties': PropValueMap({
            }),
            'properties': PropValueMap({
            }),
            'deployment_location': PropValueMap({
            })
          })
        self.assertEqual(str(context.exception), 'Request must have a lifecycle_name')

        with self.assertRaises(ValueError) as context:
          self.ansible_processor.run_lifecycle({
            'request_id': uuid.uuid4().hex,
            'lifecycle_name': 'install',
            'system_properties': PropValueMap({
            }),
            'properties': PropValueMap({
            }),
            'deployment_location': {
            }
          })
        self.assertEqual(str(context.exception), 'Request must have a lifecycle_path')

    # @patch("ansibledriver.service.ansible.AnsibleClient")
    # def test_run_lifecycle(self, mock_ansible_client):
    def test_run_lifecycle(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout
        request_id = uuid.uuid4().hex

        lifecycle_execution = LifecycleExecution(request_id, STATUS_COMPLETE, None, {
          'prop1': 'output__value1'
        })

        mock_ansible_client = PickableMock()
        mock_ansible_client.run_lifecycle_playbook.return_value = lifecycle_execution
        self.build_processor(mock_ansible_client)

        self.ansible_processor.run_lifecycle({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          },
          'request_id': request_id
        })

        # self.response_queue.next.call_args == LifecycleExecutionMatcher(lifecycle_execution)

        # self.response_queue.next.assert_called_with(LifecycleExecutionMatcher(lifecycle_execution))

        # args, kwargs = self.response_queue.next.call_args
        # self.assertEqual(kwargs, {})
        # self.assertEqual(len(args), 1)
        # self.assertEqual(args[0], LifecycleExecutionMatcher(lifecycle_execution))



        self.check_response(mock_ansible_client, lifecycle_execution)

    def test_shutdown(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout  
        
        mock_ansible_client = PickableMock()
        self.build_processor(mock_ansible_client)
        self.ansible_processor.shutdown()

        request_id = uuid.uuid4().hex

        self.ansible_processor.run_lifecycle({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          },
          'request_id': request_id
        })

        # self.response_queue.next.assert_called_with(LifecycleExecutionMatcher(lifecycle_execution))

        self.check_response(mock_ansible_client, LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INSUFFICIENT_CAPACITY, "Driver is inactive"), {}))

    def test_max_queue_size(self):
        # this is needed to ensure logging output appears in test context - see https://stackoverflow.com/questions/7472863/pydev-unittesting-how-to-capture-text-logged-to-a-logging-logger-in-captured-o
        stream_handler.stream = sys.stdout

        request_id1 = uuid.uuid4().hex
        request_id2 = uuid.uuid4().hex

        lifecycle_execution_1 = LifecycleExecution(request_id1, STATUS_COMPLETE, None, {
              'prop1': 'output__value1'
            })
        lifecycle_execution_2 = LifecycleExecution(request_id2, STATUS_COMPLETE, None, {
              'prop2': 'output__value2'
            })
        mock_ansible_client = PickableMock()
        def side_effect(*args, **kwargs):
          return sleep(request_id1, lifecycle_execution_1)
        mock_ansible_client.run_lifecycle_playbook.side_effect = side_effect

        # with a queue size of 1
        property_groups = PropertyGroups()
        property_groups.add_property_group(AnsibleProperties())
        process_properties = ProcessProperties()
        setattr(process_properties, 'max_queue_size', 1)
        property_groups.add_property_group(process_properties)
        property_groups.add_property_group(CacheProperties())
        configuration = BootstrapApplicationConfiguration(app_name='test', property_sources=[], property_groups=property_groups, service_configurators=[], api_configurators=[], api_error_converter=None)
        self.build_processor(mock_ansible_client, configuration)

        self.ansible_processor.run_lifecycle({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          },
          'request_id': request_id1
        })

        self.ansible_processor.run_lifecycle({
          'lifecycle_name': 'install',
          'lifecycle_path': DirectoryTree(self.tmp_workspace),
          'system_properties': PropValueMap({
          }),
          'properties': PropValueMap({
          }),
          'deployment_location': {
          },
          'request_id': request_id2
        })

        self.check_responses([LifecycleExecution(request_id2, STATUS_FAILED, FailureDetails(FAILURE_CODE_INSUFFICIENT_CAPACITY, "Request cannot be handled, driver is overloaded"), {}),
          lifecycle_execution_1])
