import logging
import unittest
from unittest.mock import patch, MagicMock, ANY
from ansibledriver.model.kubeconfig import KubeConfig
from ansibledriver.model.kubeconfig import K8S_SERVER_PROP, K8S_TOKEN_PROP, K8S_CERT_AUTH_DATA_PROP, K8S_CLIENT_CERT_DATA_PROP, K8S_CLIENT_KEY_DATA_PROP
from ansibledriver.service.ansible import AnsibleProperties

logger = logging.getLogger()
logger.level = logging.INFO

class TestKubeConfig(unittest.TestCase):

    def test_kube_config_with_token(self):
        deployment_location = {
            'name': 'dl1',
            'properties': {
                K8S_SERVER_PROP: "http://localhost:8080",
                K8S_TOKEN_PROP: "token"
            }
        }
        c = KubeConfig(deployment_location, AnsibleProperties())
        self.assertEqual(c.kubeConfig, {
            "apiVersion": "v1",
            "clusters": [{
                "name": "mycluster",
                "cluster": {
                    "insecure-skip-tls-verify": True,
                    "server": "http://localhost:8080"
                }
            }],
            "contexts": [{
                "name": "mycluster-context",
                "context": {
                    "cluster": "mycluster",
                    "user": "ald-user"
                }
            }],
            "current-context": "mycluster-context",
            "kind": "Config",
            "preferences": {},
            "users": [{
                "name": "ald-user",
                "user": {
                    "token": "token"
                }
            }]
        })

    def test_kube_config_with_certificate(self):
        deployment_location = {
            'name': 'dl1',
            'properties': {
                K8S_SERVER_PROP: "http://localhost:8080",
                K8S_CERT_AUTH_DATA_PROP: "cert_auth",
                K8S_CLIENT_CERT_DATA_PROP: "client_cert",
                K8S_CLIENT_KEY_DATA_PROP: "client_key"
            }
        }
        c = KubeConfig(deployment_location, AnsibleProperties())
        self.assertEqual(c.kubeConfig, {
            "apiVersion": "v1",
            "clusters": [{
                "name": "mycluster",
                "cluster": {
                    "insecure-skip-tls-verify": False,
                    "server": "http://localhost:8080",
                    "certificate-authority-data": "cert_auth"
                }
            }],
            "contexts": [{
                "name": "mycluster-context",
                "context": {
                    "cluster": "mycluster",
                    "user": "ald-user"
                }
            }],
            "current-context": "mycluster-context",
            "kind": "Config",
            "preferences": {},
            "users": [{
                "name": "ald-user",
                "user": {
                    "client-certificate-data": "client_cert",
                    "client-key-data": "client_key"
                }
            }]
        })

    def test_kube_config_missing_credentials(self):
        deployment_location = {
            'name': 'dl1',
            'properties': {
                K8S_SERVER_PROP: "123"
            }
        }
        with self.assertRaises(ValueError) as exc:
            KubeConfig(deployment_location, AnsibleProperties())
            self.assertEqual(exc.message, "Must specify either {0}, {1}, {2} or {3}".format(K8S_CERT_AUTH_DATA_PROP, K8S_CLIENT_CERT_DATA_PROP, K8S_CLIENT_KEY_DATA_PROP, K8S_TOKEN_PROP))