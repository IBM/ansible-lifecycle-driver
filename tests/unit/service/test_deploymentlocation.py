import logging
import os
import unittest
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ignition.utils.propvaluemap import PropValueMap
from ansibledriver.model.deploymentlocation import DeploymentLocation


logger = logging.getLogger()
logger.level = logging.INFO



EXAMPLE_KUBECTL_CONFIG = '''
{
    'apiVersion': 'v1',
    'clusters': [
        {'cluster': {'server': 'localhost'}, 'name': 'kubernetes'}
    ],
    'contexts': [
        {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetes'}
    ],
    'current-context': 'kubernetes-admin@kubernetes',
    'kind': 'Config',
    'preferences': {},
    'users': [
        {'name': 'kubernetes-admin', 'user': {}}
    ]
}
'''

class TestDeploymentLocation(unittest.TestCase):

    def setUp(self):
        pass

    def __propvaluemap(self, orig_props):
        props = {}
        for k, v in orig_props.items():
            props[k] = {'type': 'string', 'value': v}
        return PropValueMap(props)

    def test_deployment_location_is_none(self):
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            location = DeploymentLocation(None)
            self.assertEqual(str(context.exception), 'Deployment Location must be provided')

    def test_deployment_location_not_an_object(self):
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            location = DeploymentLocation('123')
            self.assertEqual(str(context.exception), 'Deployment Location must be an object')

    def test_deployment_location_no_type(self):
        deployment_location = {
            'name': 'dl',
            'properties': {
            }
        }
        with self.assertRaises(InvalidDeploymentLocationError) as context:
            location = DeploymentLocation(deployment_location)
            self.assertEqual(str(context.exception), 'Deployment location missing \'type\' value')

    def test_deployment_location_connection_type_default(self):
        deployment_location = {
            'name': 'dl',
            'type': 'Kubernetes',
            'properties': {
            }
        }
        location = DeploymentLocation(deployment_location)
        self.assertEqual(location.connection_type, 'ssh')

    def test_k8s_deployment_location(self):


        deployment_location = {
            'name': 'dl',
            'type': 'Kubernetes',
            'properties': self.__propvaluemap({
                'connection_type': 'kubectl',
                'clientConfig': EXAMPLE_KUBECTL_CONFIG
            })
        }
        location = DeploymentLocation(deployment_location)
        self.assertIsInstance(location.properties, PropValueMap)
        self.assertIsNotNone(location.kube_location)
        self.assertIsNotNone(location.properties.get('kubeconfig_path', None))
        kubeconfig_path = location.properties.get('kubeconfig_path', None)
        self.assertIsNotNone(kubeconfig_path)
        self.assertTrue(os.path.isfile(kubeconfig_path))
        location.cleanup()
        self.assertFalse(os.path.isfile(kubeconfig_path))

