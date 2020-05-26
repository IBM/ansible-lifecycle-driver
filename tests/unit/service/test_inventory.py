import logging
import os
import unittest
from ignition.utils.file import DirectoryTree
from ansibledriver.model.inventory import Inventory
from ansibledriver.exceptions import ResourcePackageError


logger = logging.getLogger()
logger.level = logging.INFO


class TestInventory(unittest.TestCase):

    def setUp(self):
        pass

    def test_inventory_missing_config_directory(self):
        with self.assertRaises(ResourcePackageError) as context:
            Inventory(DirectoryTree(os.getcwd() + '/tests/resources/ansible_with_missing_config'), 'Kubernetes')
            self.assertEqual(str(context.exception), 'Missing config directory in resource package driver files')