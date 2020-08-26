import logging
import unittest
import time
import uuid
import shutil
import os
import tempfile
import sys
import pathlib
from unittest.mock import patch, MagicMock, ANY
from ansibledriver.service.ansible import AnsibleClient, AnsibleProperties
from ansibledriver.service.process import ProcessProperties
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.utils.file import DirectoryTree
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups
from ignition.utils.propvaluemap import PropValueMap
from ignition.service.templating import ResourceTemplateContextService, Jinja2TemplatingService
from ansibledriver.service.rendercontext import ExtendedResourceTemplateContextService
from ignition.model.associated_topology import AssociatedTopology
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class TestAnsible(unittest.TestCase):

    def assertLifecycleExecutionEqual(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        self.assertEqual(resp.associated_topology, expected_resp.associated_topology)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertEqual(resp.failure_details.description, expected_resp.failure_details.description)

    """
    Check that the expected failure description is a substring of the returned description
    """
    def assertLifecycleExecutionMatches(self, resp, expected_resp):
        self.assertEqual(resp.status, expected_resp.status)
        self.assertEqual(resp.outputs, expected_resp.outputs)
        self.assertEqual(resp.request_id, expected_resp.request_id)
        if resp.failure_details is not None:
            if expected_resp.failure_details is None:
                self.fail('Expected failure_details to be non-null')
            self.assertEqual(resp.failure_details.failure_code, expected_resp.failure_details.failure_code)
            self.assertIn(expected_resp.failure_details.description, resp.failure_details.description)

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible')

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
            
    def test_run_lifecycle_with_input_associated_topology(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)
        try:
            request_id = uuid.uuid4().hex
            infrastructure_id_1 = uuid.uuid4().hex
            infrastructure_id_2 = uuid.uuid4().hex
            infrastructure_osp_type = 'Openstack'
            infrastructure_k8s_type = 'Kubernetes'

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
            
            associated_topology = AssociatedTopology.from_dict({
                'apache1': {
                    'id': infrastructure_id_1,
                    'type': infrastructure_osp_type
                },
                'apache2': {
                    'id': infrastructure_id_2,
                    'type': infrastructure_k8s_type
                }

            })

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_input_associated_topology')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'adopt',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'associated_topology': associated_topology,
            'keep_files': True,
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)
            
    def test_run_lifecycle_with_malformed_associated_topology_in_playbook(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)
        try:
            request_id = uuid.uuid4().hex
            infrastructure_id_1 = uuid.uuid4().hex
            infrastructure_id_2 = uuid.uuid4().hex
            infrastructure_osp_type = 'Openstack'
            infrastructure_k8s_type = 'Kubernetes'

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
            
            associated_topology = AssociatedTopology.from_dict({
                'apache1': {
                    'id': infrastructure_id_1,
                    'type': infrastructure_osp_type
                },
                'apache2': {
                    'id': infrastructure_id_2,
                    'type': infrastructure_k8s_type
                }

            })

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_with_malformed_associated_topology_in_playbook')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'adopt',
            'driver_files': DirectoryTree(dst),
            'system_properties': system_properties,
            'resource_properties': properties,
            'deployment_location': {
                'name': 'winterfell',
                'type': "Kubernetes",
                'properties': PropValueMap({
                })
            },
            'associated_topology': associated_topology,
            'keep_files': True,
            'request_id': request_id
            })

            self.assertLifecycleExecutionMatches(resp, LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, "task debug failed: {'msg': \"The task includes an option with an undefined variable. The error was: 'dict object' has no attribute 'wrong'"), {}))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)
            
    def test_run_lifecycle_return_associated_topology(self):
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
            
            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_returning_associated_topology_and_outputs')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'create',
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
            
            associated_topology = AssociatedTopology.from_dict({
                'apache1': {
                    'id': '12345678',
                    'type': 'Openstack'
                },
                'apache2': {
                    'id': '910111213',
                    'type': 'Openstack'
                }
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "Associated topology returned", 'public_ip': "10.21.28.94", 'internal_ip': "10.10.10.42"}, associated_topology))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)
            
    def ansible_missing_associated_topology_id_in_fact(self):
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
            
            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_missing_associated_topology_id_in_fact')

            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'create',
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
            
            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {}, None))
            self.assertTrue(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)