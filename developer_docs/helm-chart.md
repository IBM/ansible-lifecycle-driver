# Helm Chart

The Helm chart for this driver includes the following features:

- A Deployment to create pods for your driver application
- A Service to expose your application internally and externally (with a NodePort)
- Configurable options for:
    - Location and version of Docker image
    - Number of replicas of the driver
    - Property groups configured on your application (i.e. override the properties in the default_config file)
    - Log level
    - Pod affinity/anti-affinity
    - Node affinity/anti/affinity
    - NodePort
- Necessary Deployment labels so logs from the driver may be viewed in the dashboard provided with LM (Kibana)

# Build Helm Chart

To build the Helm chart you will need to install Helm and initialise it (e.g. `helm init --client-only` on your local machine).

## Full Build

Run the build script, the command will print the location of the generated `.tgz` Helm package.

```
python3 build.py 
```

This command will build the docker image as well, to avoid this use the skip option:

```
python3 build.py --skip-docker
```

# Deploy Helm Chart

To deploy the Helm chart will need Helm installed and initialised against a Kubernetes cluster (e.g. `helm init` on your Kubernetes cluster master node).

Install the chart with the default configuration using the install command:

```
helm install --name ansible-lifecycle-driver <path to chart>
```

Configuration for the Helm deployment can be provided with a **Helm values file** on the `-f` option. 

```
helm install --name ansible-lifecycle-driver <path to chart> -f <path to Helm values file>
```

By default, the Deployment included in this chart will expect the driver docker image to be available on the Kubernetes worker node (e.g. the image can be seen in the list returned by `docker images`). If the image is not on the node, you should [transfer the image to the node](#transfer-docker-image-to-node) or [use a docker registry](#use-docker-registry).

To override configuration for your driver application (e.g. Kafka address, other property groups configured by the user), add the following to a custom **Helm values file**:

```
app:
  override:
    ## Add the properties to configure as YAML here
    propA: valueA 
```

Once you have installed the chart you can check the status of your deployment with:

```
kubectl get pods
```

Or:

```
helm status ansible-lifecycle-driver
```

## Transfer Docker Image to Node

To transfer it to the node you can use `docker save` locally, then `docker load` on the node:

Locally:
```
docker save -o ansible-lifecycle-driver-img.tar ansible-lifecycle-driver:<release version number>
```

Transfer the file using scp:
```
scp ansible-lifecycle-driver-img.tar <user>@<worker-node-ip>:/home/<user>
```

On Node:
```
docker load -i /home/<user>/ansible-lifecycle-driver-img.tar
```

## Use Docker Registry

In a custom **Helm values file** add the following:

```
docker:
  image: <registry host and port>/ansible-lifecycle-driver
  version: <image version>
  imagePullPolicy: IfNotPresent
```

Include this values file on the Helm install command with the `-f` option.

Note: if the Docker registry is insecure you need to inform the docker daemon (usually by adding it to a "insecure-registries" in `/etc/docker/daemon.json`).
