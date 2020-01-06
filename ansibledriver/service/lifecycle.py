import uuid
import logging
from ignition.service.framework import Capability, Service, interface
from ignition.service.lifecycle import LifecycleDriverCapability
from ignition.model.lifecycle import LifecycleExecuteResponse
from ignition.utils.file import DirectoryTree

logger = logging.getLogger(__name__)

class AnsibleLifecycleDriver(Service, LifecycleDriverCapability):
    def __init__(self, ansible_processor_service, request_queue_service):
        self.ansible_processor_service = ansible_processor_service
        self.request_queue_service = request_queue_service

    def execute_lifecycle(self, lifecycle_name, lifecycle_scripts_tree, system_properties, properties, deployment_location):
        # requests are handled in sub-processes by reading off a Kafka request queue
        pass
        # request_id = uuid.uuid4().hex
        # self.request_queue_service.queue_lifecycle_request({
        #   'lifecycle_name': lifecycle_name,
        #   'lifecycle_path': lifecycle_scripts_tree.get_directory_tree('.').get_path(),
        #   'system_properties': system_properties,
        #   'properties': properties,
        #   'deployment_location': deployment_location,
        #   'request_id': request_id
        # })

        # return LifecycleExecuteResponse(request_id)

    # def execute_lifecycle_sync(self, request_id, lifecycle_name, lifecycle_path, system_properties, properties, deployment_location):
    #     self.ansible_processor_service.run_lifecycle({
    #       'lifecycle_name': lifecycle_name,
    #       'lifecycle_path': DirectoryTree(lifecycle_path),
    #       'system_properties': system_properties,
    #       'properties': properties,
    #       'deployment_location': deployment_location,
    #       'request_id': request_id
    #     })

    #     return LifecycleExecuteResponse(request_id)

    def get_lifecycle_execution(self, request_id, deployment_location):
        # noop - the driver does not use the Ignition job queue, but sends the response directly on the lifecycle responses Kafka topic
        return None