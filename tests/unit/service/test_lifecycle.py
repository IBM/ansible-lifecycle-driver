import unittest
import uuid
import time
from unittest.mock import patch, MagicMock, ANY
from ignition.model.lifecycle import LifecycleExecuteResponse, LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND, FAILURE_CODE_INSUFFICIENT_CAPACITY
from ansibledriver.service.lifecycle import AnsibleLifecycleDriver, AdditionalLifecycleProperties
from ignition.utils.file import DirectoryTree

class TestLifecycle(unittest.TestCase):

    def setUp(self):
        self.mock_ansible_processor_service = MagicMock()
        self.lifecycle_driver = AnsibleLifecycleDriver(self.mock_ansible_processor_service, AdditionalLifecycleProperties())

    def assertLifecycleExecutionEqual(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertEqual(resp.failure_details.description, expected_resp.failure_details.description)

    def test_run_lifecycle(self):
        resp = self.lifecycle_driver.execute_lifecycle('install', DirectoryTree('./'), {}, {}, {})
        self.assertIsNotNone(resp)
        self.assertIsNotNone(resp.request_id)