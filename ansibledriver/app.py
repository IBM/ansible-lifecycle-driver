import logging
import ignition.boot.api as ignition
import ansibledriver.config as ansibledriverconfig
import pathlib
import os
from ignition.boot.config import BootProperties
from ansibledriver.service.ansible import AnsibleProperties
from ansibledriver.service.process import ProcessProperties
from ansibledriver.service.resourcedriver import AdditionalResourceDriverProperties
from ansibledriver.service.config import AnsibleServiceConfigurator, AnsibleDriverHandlerConfigurator

default_config_dir_path = str(pathlib.Path(ansibledriverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'ald_config.yml')

logger = logging.getLogger('kafka')
logger.setLevel('WARN')

def create_app():
    app_builder = ignition.build_resource_driver('AnsibleLifecycleDriver')
    app_builder.include_file_config_properties(default_config_path, required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/ald/ald_config.yml', required=False)
    app_builder.include_environment_config_properties('AVD_CONFIG', required=False)

    # Using custom versions of some bootstrapped components
    boot_config = app_builder.property_groups.get_property_group(BootProperties)
    boot_config.progress_event_log.serializer_service_enabled = False

    app_builder.add_property_group(AnsibleProperties())
    app_builder.add_property_group(ProcessProperties())
    app_builder.add_property_group(AdditionalResourceDriverProperties())
    app_builder.add_service_configurator(AnsibleServiceConfigurator())
    app_builder.add_service_configurator(AnsibleDriverHandlerConfigurator())

    return app_builder.configure()

def init_app():
    app = create_app()
    return app.run()
