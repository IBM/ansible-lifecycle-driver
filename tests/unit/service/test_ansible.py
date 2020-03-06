import logging
import unittest
import time
import uuid
import shutil
import os
import sys
from unittest.mock import patch, MagicMock, ANY
from ansibledriver.service.ansible import AnsibleClient, AnsibleProperties
from ansibledriver.service.cache import CacheProperties
from ansibledriver.service.process import ProcessProperties
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.utils.file import DirectoryTree
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.utils.propvaluemap import PropValueMap

logger = logging.getLogger()
logger.level = logging.INFO

class TestAnsible(unittest.TestCase):

    def assertLifecycleExecutionEqual(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertEqual(resp.failure_details.description, expected_resp.failure_details.description)

    def setUp(self):
        property_groups = PropertyGroups()
        property_groups.add_property_group(AnsibleProperties())
        property_groups.add_property_group(ProcessProperties())
        property_groups.add_property_group(CacheProperties())
        self.configuration = BootstrapApplicationConfiguration(app_name='test', property_sources=[], property_groups=property_groups, service_configurators=[], api_configurators=[], api_error_converter=None)
        self.ansible_client = AnsibleClient(self.configuration)

    def test_run_lifecycle(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)
        try:
            request_id = uuid.uuid4().hex

            properties = PropValueMap({
                'hello_world_private_ip': {
                    'value': '10.220.217.113',
                    'type': 'string'
                },
                'ansible_ssh_user': {
                    'value': 'accanto',
                    'type': 'string'
                },
                'ansible_ssh_pass': {
                    'value': 'accanto',
                    'type': 'string'
                },
                'ansible_become_pass': {
                    'value': 'accanto',
                    'type': 'string'
                }
            })
            system_properties = PropValueMap({
            })

            cwd = os.getcwd()
            src = cwd + '/tests/resources/ansible'
            dst = cwd + '/tests/resources/ansible-copy'
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'lifecycle_path': DirectoryTree(dst),
            'system_properties': system_properties,
            'properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "type",
                'properties': PropValueMap({
                })
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    def test_run_lifecycle_keep_scripts(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)
        try:
            request_id = uuid.uuid4().hex

            properties = PropValueMap({
                'hello_world_private_ip': {
                    'value': '10.220.217.113',
                    'type': 'string'
                },
                'ansible_ssh_user': {
                    'value': 'accanto',
                    'type': 'string'
                },
                'ansible_ssh_pass': {
                    'value': 'accanto',
                    'type': 'string'
                },
                'ansible_become_pass': {
                    'value': 'accanto',
                    'type': 'string'
                }
            })
            system_properties = PropValueMap({
            })

            cwd = os.getcwd()
            src = cwd + '/tests/resources/ansible'
            dst = cwd + '/tests/resources/ansible-copy'
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'lifecycle_path': DirectoryTree(dst),
            'system_properties': system_properties,
            'properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "type",
                'properties': PropValueMap({
                })
            },
            'keep_scripts': True,
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)