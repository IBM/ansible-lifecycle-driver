import logging
import unittest
import time
import uuid
import shutil
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock, ANY
from ansibledriver.service.ansible import AnsibleClient, AnsibleProperties
from ansibledriver.service.process import ProcessProperties
from ansibledriver.service.rendercontext import ExtendedResourceTemplateContextService
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.utils.file import DirectoryTree
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.utils.propvaluemap import PropValueMap
from ignition.service.templating import ResourceTemplateContextService, Jinja2TemplatingService
from ignition.model.references import FindReferenceResult, FindReferenceResponse
from ignition.model.associated_topology import AssociatedTopologyEntry, AssociatedTopology, RemovedTopologyEntry


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
        self.configuration = BootstrapApplicationConfiguration(app_name='test', property_sources=[], property_groups=property_groups, service_configurators=[], api_configurators=[], api_error_converter=None)
        render_context_service = ExtendedResourceTemplateContextService()
        templating = Jinja2TemplatingService()
        self.ansible_client = AnsibleClient(self.configuration, templating=templating, render_context_service=render_context_service)

    def __copy_directory_tree(self, src):
        temp_dir = tempfile.mkdtemp(prefix="")
        shutil.rmtree(temp_dir, ignore_errors=True)
        dst = os.path.join(temp_dir, str(uuid.uuid4()))
        shutil.copytree(src, dst)
        return dst

    '''
    Kubernetes deployment location with Kubernetes-specific inventory
    '''
    def test_run_lifecycle_with_kubernetes_inventory(self):
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

            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    Kubernetes deployment location with default inventory
    '''
    def test_run_kubernetes_lifecycle_with_default_inventory(self):
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

            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible3')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    Kubernetes deployment location with legacy Kubernetes-specific inventory (inventory.k8s)
    '''
    def test_run_kubernetes_lifecycle_with_legacy_inventory(self):
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

            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible-with-legacy-k8s-inventory')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    deployment location with missing inventory in driver files
    '''
    def test_run_lifecycle_with_missing_inventory(self):
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

            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible-with-missing-inventory')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    def test_run_lifecycle_keep_files(self):
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

            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'install',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'keep_files': True,
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    def test_run_find(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)

        try:
            dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible')

            instance_name = "instance1"
            driver_files = DirectoryTree(dst)
            deployment_location = {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            }

            expected_associated_topology = AssociatedTopology()
            expected_properties = {
                "prop1": "value1",
                "prop2": "value2"
            }

            resp = self.ansible_client.run_find_playbook(instance_name, driver_files, deployment_location)

            self.assertLifecycleExecutionEqual(resp, FindReferenceResponse(FindReferenceResult(instance_name, expected_associated_topology, expected_properties)))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)