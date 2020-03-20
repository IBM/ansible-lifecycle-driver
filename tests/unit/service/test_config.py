import unittest
import logging
import sys
from unittest.mock import call, patch, MagicMock, ANY, DEFAULT
from ignition.boot.config import BootstrapApplicationConfiguration, BootProperties
from ignition.service.messaging import MessagingProperties
from ignition.service.lifecycle import LifecycleProperties
from ansibledriver.service.process import AnsibleProcessorService, ProcessProperties

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.mock_request_queue_service = MagicMock()
        self.mock_messaging_service = MagicMock()
        self.mock_ansible_client = MagicMock()

        self.configuration = BootstrapApplicationConfiguration()
        self.configuration.app_name = "TestApp"
        self.configuration.property_groups.add_property_group(BootProperties())
        messaging_conf = MessagingProperties()
        messaging_conf.connection_address = "kafka"
        self.configuration.property_groups.add_property_group(messaging_conf)
        self.configuration.property_groups.add_property_group(LifecycleProperties())
        process_properties = ProcessProperties()
        process_properties.process_pool_size = 1
        self.configuration.property_groups.add_property_group(process_properties)

    def test_init_processor_service_without_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            AnsibleProcessorService(self.configuration, self.mock_ansible_client, request_queue_service=self.mock_request_queue_service)
        self.assertEqual(str(context.exception), 'messaging_service argument not provided')

    def test_init_processor_service_withoutrequest_queue_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            AnsibleProcessorService(self.configuration, self.mock_ansible_client, messaging_service=self.mock_messaging_service)
        self.assertEqual(str(context.exception), 'request_queue_service argument not provided')

    def test_configure_ansible_processor_service(self):
        ansible_processor_service = AnsibleProcessorService(self.configuration, self.mock_ansible_client, request_queue_service=self.mock_request_queue_service, messaging_service=self.mock_messaging_service)
        ansible_processor_service.shutdown()
