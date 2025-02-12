import logging
import sysconfig
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
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR
import ansibledriver.ibm_cp4na_log_message as ibm_cp4na_log_message

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class EmptyEventLogger:
    
    def add(self, event):
        pass

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
        self.ansible_client = AnsibleClient(self.configuration, templating=templating, render_context_service=render_context_service, event_logger=EmptyEventLogger())

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
                },
                'bool_prop': {
                    'value': True,
                    'type': 'boolean'
                },
                'int_prop': {
                    'value': 123,
                    'type': 'integer'
                },
                'float_prop': {
                    'value': 1.2,
                    'type': 'float'
                },
                'timestamp_prop': {
                    'value': '2020-11-23T11:49:33.308703Z',
                    'type': 'timestamp'
                },
                'map_prop': {
                    'value': {
                        'A': 1,
                        'B': 'A string'
                    },
                    'type': 'map'
                },
                'list_prop': {
                    'value': ['a', 'b', 'c'],
                    'type': 'list'
                },
                'custom_type_prop': {
                    'value': {
                        'name': 'Testing',
                        'age': 42
                    },
                    'type': 'MyCustomType'
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
                },
                'bool_prop': {
                    'value': True,
                    'type': 'boolean'
                },
                'int_prop': {
                    'value': 123,
                    'type': 'integer'
                },
                'float_prop': {
                    'value': 1.2,
                    'type': 'float'
                },
                'timestamp_prop': {
                    'value': '2020-11-23T11:49:33.308703Z',
                    'type': 'timestamp'
                },
                'map_prop': {
                    'value': {
                        'A': 1,
                        'B': 'A string'
                    },
                    'type': 'map'
                },
                'list_prop': {
                    'value': ['a', 'b', 'c'],
                    'type': 'list'
                },
                'custom_type_prop': {
                    'value': {
                        'name': 'Testing',
                        'age': 42
                    },
                    'type': 'MyCustomType'
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

    def test_run_lifecycle_with_outputs_of_different_types(self):
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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_outputs')

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

            expected_outputs = {
                'string_prop': 'Hello',
                'int_prop': 1,
                'float_prop': 1.2,
                'bool_prop': True,
                'timestamp_prop': '2020-11-23T11:49:33.308703Z',
                'map_prop': {     
                    'A': 'ValueA',
                    'B': 123
                },
                'list_prop': ['A', 'B'],
                'custom_type_prop': {
                    'name': 'Testing',
                    'age': 42
                }
            }

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, expected_outputs))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    ibm_cp4na_log_message module test
    '''
    def test_run_lifecycle_with_ibm_cp4na_log_message_module(self):
        # copying ibm_cp4na_log_message module in ansible module directory under site-packages 
        site_packages_path = sysconfig.get_paths()["purelib"]
        ansible_module_path = os.path.join(site_packages_path, 'ansible', 'modules')
        print("ansible_module_path - ", ansible_module_path)
        shutil.copy(ibm_cp4na_log_message.__file__, ansible_module_path)

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

            resource_path = os.path.join(os.getcwd(), 'tests', 'resources', 'ansible_with_ibm_cp4na_log_message_module')
            dst = self.__copy_directory_tree(resource_path)
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

    '''
    invalid lifecycle name failure test
    '''
    def test_run_lifecycle_with_invalid_lifecycle(self):

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_with_invalid_lifecycle_name_in_playbook')
            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'downgrade',
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

            self.assertLifecycleExecutionMatches(resp, LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "No playbook found to run for lifecycle downgrade for request "+request_id), {}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    Valid lifecycle name success test
    '''
    def test_run_lifecycle_with_valid_lifecycle(self):

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_with_invalid_lifecycle_name_in_playbook')
            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'Install',
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
    Test complete playbook execution with failed task having ignore_errors as true
    '''
    def test_run_lifecycle_with_ignore_errors(self):

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_with_ignore_error_in_playbook')
            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'Install',
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

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there again!"}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)

    '''
    Test failed playbook execution with failed task not having ignore_errors
    '''
    def test_run_lifecycle_without_ignore_errors(self):

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_without_ignore_error_in_playbook')
            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'Install',
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

            self.assertLifecycleExecutionMatches(resp, LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, "failed - invalid machine."), {'msg': 'hello there!'}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)


    '''
    Test failed playbook execution with failed task having ignore_errors as false
    '''
    def test_run_lifecycle_with_ignore_errors_false(self):

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

            dst = self.__copy_directory_tree(str(pathlib.Path(__file__).parent.absolute()) + '/../../resources/ansible_with_ignore_error_false_in_playbook')
            resp = self.ansible_client.run_lifecycle_playbook({
            'lifecycle_name': 'Install',
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

            self.assertLifecycleExecutionMatches(resp, LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, "failed - invalid machine."), {'msg': 'hello there!'}))
            self.assertFalse(os.path.exists(dst))
        finally:
            logger.removeHandler(stream_handler)