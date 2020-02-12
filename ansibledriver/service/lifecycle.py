import uuid
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.lifecycle import LifecycleDriverCapability
from ignition.model.lifecycle import LifecycleExecuteResponse

logger = logging.getLogger(__name__)


class AdditionalLifecycleProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('lifecycle')
        self.keep_scripts = False

class AnsibleLifecycleDriver(Service, LifecycleDriverCapability):
    def __init__(self, ansible_processor_service, additional_lifecycle_properties):
        self.ansible_processor_service = ansible_processor_service
        self.additional_lifecycle_properties = additional_lifecycle_properties

    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        request_id = uuid.uuid4().hex

        self.ansible_processor_service.run_lifecycle({
          'lifecycle_name': lifecycle_name,
          'lifecycle_path': lifecycle_scripts_tree,
          'system_properties': system_properties,
          'properties': properties,
          'deployment_location': deployment_location,
          'request_id': request_id
        }, keep_scripts=self.additional_lifecycle_properties.keep_scripts)

        return LifecycleExecuteResponse(request_id)

    def get_lifecycle_execution(self, request_id, deployment_location):
        # noop - the driver does not use the Ignition job queue, but sends the response directly on the lifecycle responses Kafka topic
        return None