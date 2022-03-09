# Install to Kubernetes

The following guide details how to install the Ansible Lifecycle Driver into a Kubernetes environment with helm.

## Prerequisites
To complete the install you will need a Kubernetes cluster.

You will also need a controller machine (can be one of the Kubernetes cluster nodes) to perform the installation from. This machine must have the Helm CLI tool installed and initialised with access to your cluster.

## Installation

### Download

Download the Helm chart from the [releases](https://github.com/IBM/ansible-lifecycle-driver/releases) page to your machine.

```
wget https://github.com/IBM/ansible-lifecycle-driver/releases/download/<version>/ansiblelifecycledriver-<version>.tgz
```

### Install 

Install the chart using the helm CLI:

```
helm install ansiblelifecycledriver-<version>.tgz --name ansible-lifecycle-driver [--set app.config.override.lifecycle.request_queue.topic.num_partitions=100,app.config.override.lifecycle.request_queue.topic.replication_factor=1]
```

By default, the driver will attempt to connect to Kafka with the address `alm-kafka:9092`.  For [All In One](https://github.com/accanto-systems/lm-allinone) it should be set to `foundation-kafka:9092`:

```
helm install ansiblelifecycledriver-<version>.tgz --name ansible-lifecycle-driver --set app.config.override.messaging.connection_address=foundation-kafka:9092
```

The Ansible Lifecycle Driver uses an Ignition [Request Queue](https://github.com/IBM/ignition/blob/master/docs/user-guide/framework/bootstrap-components/request_queue.md) to process transitions. Note the overrides for the Kafka request queue topic number of partitions and replication factory. The number of partitions determines an upper limit on how many transitions can be run in parallel, the replication factor improves fault tolerance and should be set to less than or equal to the number of Kafka brokers in your cluster.

The driver runs with SSL enabled by default. The installation will generate a self-signed certificate and key by default, adding them to the Kubernetes secret "ald-tls". To use a custom certificate and key in your own secret, override the properties under "apps.config.security.ssl.secret".

### Confirm

You can confirm the driver is working accessing: ```http://<kubernetes-node-ip>:{(helm.node_port)}/management/health```