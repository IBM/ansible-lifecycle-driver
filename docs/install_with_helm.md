# Install to Kubernetes

The following guide details how to install the Ansible Lifecycle Driver into a Kubernetes environment with helm.

## Install Helm Chart

Download and install the chart using the helm CLI:

```
helm install ansiblelifecycledriver-<version>.tgz --name ansible-lifecycle-driver
```

The above installation will expect Kafka to be running in the same Kubernetes namespace with name `foundation-kafka`, which is the default installed by Stratoss&trade; Lifecycle Manager. If different, override the Kafka address:

```
helm install ansiblelifecycledriver-<version>.tgz --name ansible-lifecycle-driver --set app.config.override.messaging.connection_address=myhost:myport
```

The driver runs with SSL enabled by default. The installation will generate a self-signed certificate and key by default, adding them to the Kubernetes secret "ald-tls". To use a custom certificate and key in your own secret, override the properties under "apps.config.security.ssl.secret".

# Access Swagger UI

The Swagger UI can be found at `https://your_host:31680/api/lifecycle/ui` e.g. `http://localhost:31680/api/lifecycle/ui`
