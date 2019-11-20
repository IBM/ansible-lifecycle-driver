import yaml

K8S_SERVER_PROP = 'k8s-server'
K8S_USERNAME_PROP = 'k8s-username'
K8S_CERT_AUTH_DATA_PROP = 'k8s-certificate-authority-data'
K8S_CLIENT_CERT_DATA_PROP = 'k8s-client-certificate-data'
K8S_CLIENT_KEY_DATA_PROP = 'k8s-client-key-data'
K8S_TOKEN_PROP = 'k8s-token'
K8S_NAMESPACE_PROP = "k8s-namespace"
REGISTRY_URI_PROP = 'registry_uri'

class KubeConfig():
    def __init__(self, deployment_location):
        self.name = deployment_location.get('name', None)
        if self.name is None:
            raise ValueError('Must specify a name for the deployment location')

        dl_properties = deployment_location.get('properties', None)
        if dl_properties is None:
            raise ValueError('Deployment location has no properties')

        k8sServer = dl_properties.get(K8S_SERVER_PROP, None)
        if k8sServer is None:
            raise ValueError('Deployment location properties must contain a value for {0}'.format(K8S_SERVER_PROP))

        k8sToken = dl_properties.get(K8S_TOKEN_PROP, None)
        certificateAuthorityData = dl_properties.get(K8S_CERT_AUTH_DATA_PROP, None)
        clientCertificateData = dl_properties.get(K8S_CLIENT_CERT_DATA_PROP, None)
        clientKeyData = dl_properties.get(K8S_CLIENT_KEY_DATA_PROP, None)

        if certificateAuthorityData is not None and clientCertificateData is not None and clientKeyData is not None:
            cluster = {
                "insecure-skip-tls-verify": False,
                "server": k8sServer,
                "certificate-authority-data": certificateAuthorityData
            }
            user = {
                "client-certificate-data": clientCertificateData,
                "client-key-data": clientKeyData
            }
        elif k8sToken is not None:
            cluster = {
                "insecure-skip-tls-verify": True,
                "server": k8sServer
            }
            user = {
                "token": k8sToken
            }
        else:
            raise ValueError('Must specify either {0}, {1}, {2} or {3}'.format(K8S_CERT_AUTH_DATA_PROP, K8S_CLIENT_CERT_DATA_PROP, K8S_CLIENT_KEY_DATA_PROP, K8S_TOKEN_PROP))

        self.kubeConfig = {
            "apiVersion": "v1",
            "clusters": [{
                "name": "mycluster",
                "cluster": cluster
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
                "user": user
            }]
        }

    def write(self):
        filename = '/var/ald/dl_' + self.name + '.yml'
        with open(filename, 'w') as outfile:
            yaml.dump(self.kubeConfig, outfile, default_flow_style=False)
        return filename