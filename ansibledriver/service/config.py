import pathlib
import os
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.framework import ServiceRegistration
from ignition.service.lifecycle import LifecycleMessagingCapability
from ignition.service.requestqueue import RequestQueueCapability
import ansibledriver.api_specs as api_specs
from ansibledriver.service.process import AnsibleProcessorCapability, AnsibleProcessorService
from ansibledriver.service.ansible import AnsibleClient
from ansibledriver.service.lifecycle import AnsibleLifecycleDriver, AdditionalLifecycleProperties


class AnsibleServiceConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(AnsibleProcessorService, configuration, AnsibleClient(configuration), request_queue_service=RequestQueueCapability, messaging_service=LifecycleMessagingCapability))

class AnsibleDriverConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(AnsibleLifecycleDriver, ansible_processor_service=AnsibleProcessorCapability, request_queue_service=RequestQueueCapability, additional_lifecycle_properties=AdditionalLifecycleProperties))

