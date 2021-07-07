# Docker Image

The Docker image for this driver includes the following features:

- Installs the driver from a `whl` file created with standard Python setuptools
- Runs the `ald` command to start the driver application with a uwsgi container (standard for Python production applications)
- Supports installing a development version of Ignition from a `whl` file
- Supports configuring the uWSGI container implementation used at both build and runtime (also includes configuring the number of processes and threads used by uWSGI container)

## Automated

```
python3 build.py 
```

If you need to include a development version of Ignition you must specify the path to the whl for it:

```
python3 build.py --ignition-whl /path/to/ignition.whl
```

## Manual Build Docker Image

This guide shows you how to build the Docker image without the build.py script

### 1. Build Python Wheel

This requires `setuptools` and `wheel` to be installed:

```
python3 -m pip install --user --upgrade setuptools wheel
```

Run the `setup.py` script at the root of the project to produce a whl (found in `dist/`):

```
python3 setup.py bdist_wheel
```

### 2. Build Docker Image

This requires `docker` to be installed and running on your local machine.

Move the whl now in `dist` to the `docker/whls` directory (create the `whls` directory if it does not exist. Ensure no additional whls are in this directory if it does)

```
rm -rf ./docker/whls
mkdir ./docker/whls
cp dist/ansible_lifecycle_driver-<release version number>-py3-none-any.whl docker/whls/
```

If you need a development version of Ignition, you must build the whl for it and copy it to this directory also.

Navigate to the Docker directory and build the image. Tag with the release version number.

```
cd docker
docker build -t ansible-lifecycle-driver:<release version number> .
```