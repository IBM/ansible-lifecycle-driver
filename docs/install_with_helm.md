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

# Access Swagger UI

The Swagger UI can be found at `http://your_host:31680/api/lifecycle/ui` e.g. `http://localhost:31680/api/lifecycle/ui`
