import os
from tempfile import NamedTemporaryFile
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ansibledriver.exceptions import ResourcePackageError


INVENTORY = "inventory"


class Inventory():
  def __init__(self, driver_files, infrastructure_type):
    self.driver_files = driver_files
    if not self.driver_files.has_directory('config'):
      raise ResourcePackageError('Missing config directory in resource package driver files')
    if infrastructure_type is None:
        raise InvalidDeploymentLocationError('Deployment location missing \'type\' value')
    self.infrastructure_type = infrastructure_type

  def get_inventory_path(self):
    config_path = self.driver_files.get_directory_tree('config')
    subpath = f'{INVENTORY}.{self.infrastructure_type}'
    if not config_path.has_file(subpath):
      if self.infrastructure_type == 'Kubernetes':
        subpath = f'{INVENTORY}.k8s'
        if not config_path.has_file(subpath):
          subpath = f'{INVENTORY}'
      else:
        subpath = f'{INVENTORY}'

    if not config_path.has_file(subpath):
      # create default inventory file
      # TODO could do with Ignition support for calling config_path.get_path without throwing an exception for missing path
      with open(os.path.join(config_path.get_path(), subpath), "w") as inventory_file:
        inventory_file.write('[run_hosts]\n')
        inventory_file.write('localhost ansible_connection=local ansible_python_interpreter="/usr/bin/env python3" host_key_checking=False')
        inventory_file.close()

    return config_path.get_file_path(subpath)