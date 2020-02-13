import pathlib
import os
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.framework import ServiceRegistration
from ignition.service.lifecycle import LifecycleMessagingCapability
import ansibledriver.api_specs as api_specs
from ansibledriver.service.process import AnsibleProcessorCapability, AnsibleProcessorService
from ansibledriver.service.queue import RequestQueue, ResponseQueue
from ansibledriver.service.ansible import AnsibleClient
from ansibledriver.service.lifecycle import AnsibleLifecycleDriver, AdditionalLifecycleProperties

# Grabs the __init__.py from the api_specs package then takes it's parent, the api directory itself
api_spec_path = str(pathlib.Path(api_specs.__file__).parent.resolve())

class AnsibleServiceConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(AnsibleProcessorService, configuration, RequestQueue(), ResponseQueue(), AnsibleClient(configuration), messaging_service=LifecycleMessagingCapability))

class AnsibleDriverConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(AnsibleLifecycleDriver, ansible_processor_service=AnsibleProcessorCapability, additional_lifecycle_properties=AdditionalLifecycleProperties))

class AnsibleApiConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register, service_instances, api_register):
        self.__configure_api_spec(configuration, service_register, service_instances, api_register)

    def __configure_api_spec(self, configuration, service_register, service_instances, api_register):
        api_spec = os.path.join(api_spec_path, 'ansible.yaml')
        api_service_class = service_register.get_service_offering_capability(AnsibleProcessorCapability)
        if api_service_class is None:
            raise ValueError('No service has been registered with the AnsibleProcessorCapability')
        api_service_instance = service_instances.get_instance(api_service_class)
        if api_service_instance is None:
            raise ValueError('No instance of the AnsibleProcessorCapability service has been built')
        api_register.register_api(api_spec, resolver=build_resolver_to_instance(api_service_instance))
