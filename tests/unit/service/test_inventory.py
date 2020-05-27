import logging
import os
import unittest
import uuid
import shutil
import tempfile
from ignition.utils.file import DirectoryTree
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ansibledriver.model.inventory import Inventory
from ansibledriver.exceptions import ResourcePackageError


logger = logging.getLogger()
logger.level = logging.INFO


class TestInventory(unittest.TestCase):

    def setUp(self):
        pass

    def __copy_directory_tree(self, src):
        temp_dir = tempfile.mkdtemp(prefix="")
        shutil.rmtree(temp_dir, ignore_errors=True)
        dst = os.path.join(temp_dir, str(uuid.uuid4()))
        shutil.copytree(src, dst)
        return dst

    def test_inventory_missing_config_directory(self):
        with self.assertRaises(ResourcePackageError) as context:
            Inventory(DirectoryTree(os.getcwd() + '/tests/resources/ansible_with_missing_config'), 'Kubernetes')
            self.assertEqual(str(context.exception), 'Missing config directory in resource package driver files')

    def test_inventory_missing_infrastructure_type(self):
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            Inventory(DirectoryTree(os.getcwd() + '/tests/resources/ansible'), None)
            self.assertEqual(str(context.exception), 'Deployment location missing \'type\' value')

    def test_creates_temporary_inventory(self):
        dst = self.__copy_directory_tree(os.getcwd() + '/tests/resources/ansible-with-missing-inventory')
        Inventory(DirectoryTree(dst), 'Kubernetes').get_inventory_path()
        # make sure the default inventory file is created
        self.assertTrue(os.path.exists(os.path.join(dst, 'config/inventory')))
