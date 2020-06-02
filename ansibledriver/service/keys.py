import os
import logging
from tempfile import NamedTemporaryFile


logger = logging.getLogger(__name__)


class KeyPropertyProcessor():
  def __init__(self, properties, system_properties, dl_properties):
    self.properties = properties
    self.system_properties = system_properties
    self.dl_properties = dl_properties
    self.key_files = []

  """
  Process (input) key properties by writing the private key out to a file so that it can be
  referenced in e.g. inventory files.
  """
  def process_key_properties(self):
    self.process_keys(self.properties)
    self.process_keys(self.system_properties)
    self.process_keys(self.dl_properties)

  def process_keys(self, properties):
    for prop in properties.get_keys().items_with_types():
      self.write_private_key(properties, prop[0], prop[1])

  def write_private_key(self, properties, key_prop_name, private_key):
    with NamedTemporaryFile(delete=False, mode='w') as private_key_file:
      logger.debug(f'Writing private key file {private_key_file.name}')
      private_key_value = private_key.get('privateKey', None)
      private_key_file.write(private_key_value)
      private_key_file.flush()
      self.key_files.append(private_key_file)

      logger.debug('Setting property {key_prop_name}_path')
      properties[key_prop_name + '_path'] = private_key_file.name

      logger.debug('Setting property {key_prop_name}_name')
      key_name = private_key.get('keyName', None)
      properties[key_prop_name + '_name'] = key_name

  """
  Remove any private key files generated during the Ansible run.
  """
  def clear_key_files(self):
    for key_file in self.key_files:
      logger.debug('Removing private key file {0}'.format(key_file.name))
      os.unlink(key_file.name)