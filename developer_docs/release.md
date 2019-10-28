# Release

The following steps detail how the Ansible Lifecycle driver release is produced. This may only be performed by a user with admin rights to this Github, Docker and Pypi repository.

## 1. Setting the Version

1.1. Start by setting the version of the release and ignition-framework version (if update needed) in `ansibledriver/pkg_info.json`:

```
{
  "version": "<release version number>",
  "ignition-version": "==0.1.0"
}
```

1.2. Ensure the `docker.version` in `helm/ansiblelifecycledriver/values.yaml` includes the correct version number.

1.3. Ensure the `version` and `appVersion` in `helm/ansiblelifecycledriver/Chart.yaml` includes the correct version number

1.4 Push all version number changes to Github so the may be tagged by the release

## 2. Build Python Wheel

Build the python wheel by navigating to the root directory of this project and executing:

```
python3 setup.py bdist_wheel
```

The whl file is created in `dist/`

## 3. Package the docs

Create a TAR of the docs directory:

```
tar -cvzf ansible-lifecycle-driver-<release version number>-docs.tgz docs/ --transform s/docs/ansible-lifecycle-driver-<release version number>-docs/
```

On a Mac:

```
tar -cvz -s '/docs/ansible-lifecycle-driver-<release version number>-docs/' -f ansible-lifecycle-driver-<release version number>-docs.tgz docs/
```

## 4. Build Docker Image

4.1. Move the whl now in `dist` to the `docker/whls` directory (ensure no additional whls are in the docker directory)

```
cp dist/ansible_lifecycle_driver-<release version number>-py3-none-any.whl docker/whls/
```

4.2. Navigate to the `docker` directory

```
cd docker
```

4.3. Build the docker image (**tag with release version number and accanto repository**)

```
docker build -t accanto/ansible-lifecycle-driver:<release version number> .
```

## 5. Build Helm Chart

Package the helm chart (**don't forget to ensure the Chart.yaml and values.yaml have correct version numbers**)

```
helm package helm/ansiblelifecycledriver
```

## 6. Create release on Github

5.1 Navigate to Releases on the Github repository for this project and create a new release.

5.2 Ensure the version tag and title correspond with the version number set in the pkg_info file earlier. Include release notes in the description of the release.

5.3 Attach the docs archive to the release

5.4 Attach the helm chart archive to the release

5.5 Push the docker image to Dockerhub with:

```
docker push accanto/ansible-lifecycle-driver:<release version number>
```

## 7. Set next development version

Usually the next dev version should be an minor increment of the previous, with `dev0` added. For example, after releasing 0.1.0 it would be `0.2.0.dev0`.

7.1 Set the version of the next development version in `ansibledriver/pkg_info.json`:

```
{
  "version": "<next development version number>",
  "ignition-version": "<next ignition version number if different>"
}
```

7.2. Update the `docker.version` in `helm/ansiblelifecycledriver/values.yaml` to the next development version number.

7.3. Update the `version` and `appVersion` in `helm/ansiblelifecycledriver/Chart.yaml` to the next development version number.

7.4 Push version number changes to Github
