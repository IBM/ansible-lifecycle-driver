import uuid
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.resourcedriver import ResourceDriverHandlerCapability
from ignition.utils.file import DirectoryTree

logger = logging.getLogger(__name__)


class AdditionalResourceDriverProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('resource_driver')
        self.keep_scripts = False

class AnsibleDriverHandler(Service, ResourceDriverHandlerCapability):
    def __init__(self):
        pass

    def execute_lifecycle(self, lifecycle_name, driver_files, system_properties, resource_properties, request_properties, internal_resources, deployment_location):
        # requests are handled in sub-processes by reading off a Kafka request queue
        pass

    def get_lifecycle_execution(self, request_id, deployment_location):
        # noop - the driver does not use the Ignition job queue, but sends the response directly on the lifecycle responses Kafka topic
        return None

    def find_reference(self, instance_name, driver_files, deployment_location):
        return None