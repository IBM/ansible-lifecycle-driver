from ignition.locations.kubernetes import KubernetesDeploymentLocation
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND
from ignition.locations.exceptions import InvalidDeploymentLocationError
from ignition.utils.propvaluemap import PropValueMap

import logging


logger = logging.getLogger(__name__)


class DeploymentLocation():
    @staticmethod
    def from_request(request):
        return DeploymentLocation(request.get('deployment_location', None))

    def __init__(self, deployment_location):
        if deployment_location is None:
            raise InvalidDeploymentLocationError('Deployment Location must be provided')
        if not isinstance(deployment_location, dict):
            raise InvalidDeploymentLocationError('Deployment Location must be an object')
        if 'properties' not in deployment_location:
            raise InvalidDeploymentLocationError('Deployment Location must have properties')
        self.__deployment_location = deployment_location
        self.infrastructure_type = self.__deployment_location.get('type', None)
        if self.infrastructure_type is None:
            raise InvalidDeploymentLocationError('Deployment location missing \'type\' value')
        self.connection_type = self.__deployment_location['properties'].get('connection_type', None)
        if self.connection_type is None:
            self.connection_type = 'ssh'
        if self.connection_type == 'kubectl':
          self.__kube_location = KubernetesDeploymentLocation.from_dict(deployment_location)
          if self.__kube_location is not None:
            self.kubeconfig_file = self.__kube_location.write_config_file()
            logger.debug(f'Created kubeconfig file at {self.kubeconfig_file}')
            self.__deployment_location['properties']['kubeconfig_path'] = self.kubeconfig_file
          else:
            raise ValueError('Unable to convert deployment location to a Kubernetes deployment location')
        else:
          self.__kube_location = None

    def deployment_location(self):
        return self.__deployment_location

    def properties(self):
        return self.__deployment_location['properties']

    def kube_location(self):
        return self.__kube_location

    def cleanup(self):
        if self.__kube_location is not None:
            try:
                logger.debug(f'Attempting to clean up deployment location related files')
                self.__kube_location.clear_config_files()
            except Exception as e:
                logger.exception(f'Encountered an error whilst trying to clean up deployment location related files: {e}')

