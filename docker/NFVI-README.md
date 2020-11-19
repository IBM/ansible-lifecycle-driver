# NFVI 

This branch of the driver is intended to include the following additions:

Ansible Modules:
- HP One View Ansible Module

Python Modules:
- Listed in extra-requirements.txt

You'll notice that there are additional directories copied into the image for Ansible components:

- `library` - for modules
- `module_utils` - for module util functions
- `roles` - for Ansible roles
- `collections` - for Ansible collections

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

Add any extra modules/roles/collections you wish. You can see how to do this, manually or with Ansible galaxy [in these instructions](building_image_with_extra_modules.md). In short, you can add libraries, collections, roles with galaxy by directing the installation to the necessary directory:

```
ansible-galaxy collection install <collection to install> -p ./collections
```

To add Python modules, you can add it to `extra-requirements.txt`. Additions to this file **SHOULD** be pushed up to the repository.

To build the `ansible-lifecycle-driver:2.1.0.dev0.nfviautomation` docker image, run the below script from the root of this project:

```
cd ../
./build-nfvi.sh
```

You may save/copy this image to your target environment:

```
docker save ansible-lifecycle-driver:2.1.0.dev0.nfviautomation -o ald.img

scp ald.img <user>@<target host>:ald.img 
```