import logging
import unittest
import time
import uuid
import shutil
import os
import sys
import filecmp
from unittest.mock import patch, MagicMock, ANY
from ansibledriver.service.ansible import AnsibleClient, AnsibleProperties, TemplateProcessor
from ansibledriver.service.cache import CacheProperties
from ansibledriver.service.process import ProcessProperties
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.utils.file import DirectoryTree
from ignition.boot.config import BootstrapApplicationConfiguration, PropertyGroups

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

    def test_template_processor(self):
        properties = {
            'hello_world_private_ip': '10.220.217.113',
            'ansible_ssh_user': 'accanto',
            'ansible_ssh_pass': 'accanto',
            'ansible_become_pass': 'accanto',
            'jumphost_ip': '10.220.217.113',
            'jumphost_password': 'accanto',
            'jumphost_username': 'accanto'
        }
        system_properties = {
        }

        cwd = os.getcwd()
        src = cwd + '/tests/resources/ansible'
        dst = cwd + '/tests/resources/' + uuid.uuid4().hex
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        config_dir = DirectoryTree(dst)

        all_properties = {
          'properties': {
            'hello_world_private_ip': '10.220.217.113',
            'ansible_ssh_user': 'accanto',
            'ansible_ssh_pass': 'accanto',
            'ansible_become_pass': 'accanto',
            'jumphost_ip': '10.220.217.113',
            'jumphost_password': 'accanto',
            'jumphost_username': 'accanto'
          },
          'system_properties': {},
          'dl_properties': {}
        }

        TemplateProcessor(config_dir, all_properties).process_templates()

        expected_content_file = str(uuid.uuid4().hex)
        with open(expected_content_file, 'w') as f:
          f.write('''---\nansible_host: 10.220.217.113\nansible_connection: ssh\nansible_user: accanto\nansible_ssh_user: accanto\nansible_password: accanto\nansible_ssh_pass: accanto\nansible_become_pass: accanto\nssh_with_jumphost: "-o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no -o ProxyCommand='sshpass -p accanto ssh -o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no -W %h:%p accanto@10.220.217.113'"\nssh_without_jumphost: "-o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no"\nansible_ssh_common_args: "{{ ssh_with_jumphost if properties.jumphost_ip is defined else ssh_without_jumphost }}"''')
        self.assertTrue(filecmp.cmp(dst + '/config/host_vars/test-host.yml', expected_content_file))

    def test_run_lifecycle(self):
        # configure so that we can see logging from the code under test
        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)
        try:
            request_id = uuid.uuid4().hex

            properties = {
                'hello_world_private_ip': '10.220.217.113',
                'ansible_ssh_user': 'accanto',
                'ansible_ssh_pass': 'accanto',
                'ansible_become_pass': 'accanto'
            }
            system_properties = {
            }

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
                'properties': {
                }
            },
            'request_id': request_id
            })

            self.assertLifecycleExecutionEqual(resp, LifecycleExecution(request_id, STATUS_COMPLETE, None, {'msg': "hello there!"}))
        finally:
            logger.removeHandler(stream_handler)
