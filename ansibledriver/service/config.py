import pathlib
import os
from ignition.boot.connexionutils import build_resolver_to_instance
from ignition.service.framework import ServiceRegistration
from ignition.service.resourcedriver import LifecycleMessagingCapability
from ignition.service.requestqueue import LifecycleRequestQueueCapability
from ignition.service.templating import TemplatingCapability, ResourceTemplateContextCapability 
import ansibledriver.api_specs as api_specs
from ansibledriver.service.process import AnsibleProcessorCapability, AnsibleProcessorService
from ansibledriver.service.ansible import AnsibleClientCapability, AnsibleClient
from ansibledriver.service.resourcedriver import AnsibleDriverHandler, AdditionalResourceDriverProperties
from ansibledriver.service.rendercontext import ExtendedResourceTemplateContextService


class AnsibleServiceConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(ExtendedResourceTemplateContextService))
        service_register.add_service(ServiceRegistration(AnsibleClient, configuration,
            render_context_service=ResourceTemplateContextCapability,
            templating=TemplatingCapability))
        service_register.add_service(ServiceRegistration(AnsibleProcessorService, configuration,
            ansible_client=AnsibleClientCapability,
            request_queue_service=LifecycleRequestQueueCapability,
            messaging_service=LifecycleMessagingCapability))


class AnsibleDriverHandlerConfigurator():

    def __init__(self):
        pass

    def configure(self, configuration, service_register):
        service_register.add_service(ServiceRegistration(AnsibleDriverHandler,
            ansible_client=AnsibleClientCapability))
