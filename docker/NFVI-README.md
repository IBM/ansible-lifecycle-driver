# NFVI 

This branch of the driver is intended to include the following additions:

Ansible Modules:
- HP One View Ansible Module

Python Modules:
- Listed in extra-requirements.txt

# Prerequisite

These instructions assume you have Python3.6.9+ installed and a clone of this repo.

You will need the following Python libraries, which may be installed with pip:

```
python3 -m pip install -U setuptools wheel
```

# Build

You need to start from this `docker` directory:

```
cd docker
```

To build the image, you must get the HP One View source code (this is **NOT** pushed up into the repo so you must remember to do this on each build).

```
git clone https://github.com/HewlettPackard/oneview-ansible.git

cp -r oneview-ansible/library/*.py library/

cp -r oneview-ansible/library/module_utils/*.py module_utils
```

Add any extra modules you wish. If it's a Python module, you can add it to `extra-requirements.txt`. Additions to this file **SHOULD** be pushed up to the repository.

To build the image, you must first build the `.whl` file for the application. 

Go back one directory, clear out any existing builds, then execute the setup command: 

```
cd ../
rm -rf ./build
rm -rf ./dist
rm docker/whls/*

python3 setup.py bdist_wheel
```

The whl file will be created in `dist/`

Move the whl now in `dist` to the `docker/whls` directory (ensure no additional whls are in the docker directory)

```
cp dist/ansible_lifecycle_driver-<release version number>-py3-none-any.whl docker/whls/
```

Navigate back to the `docker` directory

```
cd docker
```

```
docker build -t ansible-lifecycle-driver:2.1.0.dev0.nfviautomation .
```

You may save/copy this image to your target environment:

```
docker save ansible-lifecycle-driver:2.1.0.dev0.nfviautomation -o ald.img

scp ald.img <user>@<target host>:ald.img 
```