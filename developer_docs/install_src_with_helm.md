# Run Helm Chart

You will need:

- Python
- Docker
- Helm

## Build Docker Image

To build the Docker image for the driver from this repository, do the following:

1. Build a python whl for the driver

```
python3 setup.py bdist_wheel
```

2. Move the whl now in `dist` to the `docker/whl` directory (ensure no additional whls are in the docker directory)

```
cp dist/ansible_lifecycle_driver-<driver-version>-py3-none-any.whl docker/whls/
```

If using a development version (`.dev` version) of Ignition (check `ansibledriver/pkg_info.json`) then you need to build and copy the Ignition whl to the `docker/whls` directory as well.

3. Navigate to the `docker` directory

```
cd docker
```

4. Build the docker image

```
docker build -t accanto/ansible-lifecycle-driver:<driver-version> .
```

## Run Helm Chart

Run the helm chart, setting the Docker image version if different to the default in `helm/ansiblelifecycledriver/values.yaml`:

```
helm install helm/ansiblelifecycledriver --name ansiblelifecycledriver --set docker.version=<driver-version>
```

The above installation will expect Kafka to be running in the same Kubernetes namespace with name `foundation-kafka`, which is the default installed by Stratoss&trade; Lifecycle Manager. If different, override the Kafka address:

```
helm install helm/ansiblelifecycledriver --name ansiblelifecycledriver --set app.config.override.messaging.connection_address=myhost:myport
```

# Access Swagger UI

The Swagger UI can be found at `http://your_host:31680/api/infrastructure/ui` e.g. `http://localhost:31680/api/infrastructure/ui`
