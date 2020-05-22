import logging
from ansibledriver.model.deploymentlocation import DeploymentLocation


logger = logging.getLogger()
logger.level = logging.INFO

class TestDeploymentLocation(unittest.TestCase):

    def setUp(self):
        pass

    def test_deployment_location(self):
        deployment_location = {
            'name': 'dl',
            'type': 'Kubernetes',
            'properties': {

            }
        }
        location = DeploymentLocation(deployment_location)