import unittest
import uuid
import time
from unittest.mock import patch, MagicMock, ANY
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ansibledriver.service.lifecycle import AnsibleLifecycleDriver
from ignition.utils.file import DirectoryTree

class TestLifecycle(unittest.TestCase):

    def setUp(self):
        self.mock_ansible_service = MagicMock()
        self.lifecycle = AnsibleLifecycleDriver(self.mock_ansible_service)

    def assertLifecycleExecutionEqual(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertEqual(resp.failure_details.description, expected_resp.failure_details.description)

    def get_response(self, request_id):
      for i in range(10):
        resp = self.lifecycle.get_lifecycle_execution(request_id, {})
        if resp is not None and resp.status != STATUS_IN_PROGRESS:
          return resp
        else:
          time.sleep(1)
      else:
        self.fail('Timeout waiting for response')

    def test_run_lifecycle(self):
        request_id = uuid.uuid4().hex

        self.mock_ansible_service.get_lifecycle_execution.return_value = LifecycleExecution(request_id, STATUS_COMPLETE, None, {
            'prop1': 'output__value1'
          })

        self.lifecycle.execute_lifecycle('install', DirectoryTree('./'), {}, {}, {})

        expected_resp = LifecycleExecution(request_id, STATUS_COMPLETE, None, {
            'prop1': 'output__value1'
            })

        response = self.get_response(request_id)
        self.assertLifecycleExecutionEqual(response, expected_resp)
