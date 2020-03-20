import logging
import ignition.boot.api as ignition
import ansibledriver.config as ansibledriverconfig
import pathlib
import os
from ansibledriver.service.ansible import AnsibleProperties
from ansibledriver.service.process import ProcessProperties
from ansibledriver.service.lifecycle import AdditionalLifecycleProperties
from ansibledriver.service.config import AnsibleServiceConfigurator, AnsibleDriverConfigurator

default_config_dir_path = str(pathlib.Path(ansibledriverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'ald_config.yml')

logger = logging.getLogger('kafka')
logger.setLevel('WARN')

def create_app():
    app_builder = ignition.build_vnfc_driver('AnsibleLifecycleDriver')
    app_builder.include_file_config_properties(default_config_path, required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/ald/ald_config.yml', required=False)
    app_builder.include_environment_config_properties('AVD_CONFIG', required=False)

    app_builder.add_property_group(AnsibleProperties())
    app_builder.add_property_group(ProcessProperties())
    app_builder.add_property_group(AdditionalLifecycleProperties())
    app_builder.add_service_configurator(AnsibleServiceConfigurator())
    app_builder.add_service_configurator(AnsibleDriverConfigurator())

    return app_builder.configure()

def init_app():
    app = create_app()
    return app.run()
