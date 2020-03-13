import uuid
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.lifecycle import LifecycleDriverCapability
from ignition.model.lifecycle import LifecycleExecuteResponse
from ignition.utils.file import DirectoryTree

logger = logging.getLogger(__name__)


class AdditionalLifecycleProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('lifecycle')
        self.keep_scripts = False

class AnsibleLifecycleDriver(Service, LifecycleDriverCapability):
    def __init__(self, ansible_processor_service, request_queue_service, additional_lifecycle_properties):
        self.ansible_processor_service = ansible_processor_service
        self.request_queue_service = request_queue_service
        self.additional_lifecycle_properties = additional_lifecycle_properties

    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        # requests are handled in sub-processes by reading off a Kafka request queue
        pass

    def get_lifecycle_execution(self, request_id, deployment_location):
        # noop - the driver does not use the Ignition job queue, but sends the response directly on the lifecycle responses Kafka topic
        return None