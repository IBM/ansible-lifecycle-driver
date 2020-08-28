# NFVI 

This branch of the driver is intended to include the following additions:

Ansible Modules:
- HP One View Ansible Module

Python Modules:
- hpICsp
- hpOneView
- netaddr

**NOTE:** Please keep this list up-to-date when adding modules

# Build

To build the image, you must get the HP One View source code (this is **NOT** pushed up into the repo so you must remember to do this on each build).

```
git clone https://github.com/HewlettPackard/oneview-ansible.git

cp -r oneview-ansible/library/*.py library/

cp -r oneview-ansible/library/module_utils/*.py module_utils
```

Add any extra modules you wish. If it's a Python module, you can add it to `extra-requirements.txt`. Additions to this file **SHOULD** be pushed up to the repository.

```
docker build -t ansible-lifecycle-driver:2.1.0.dev0+nfviautomation .
```

You may save/copy this image to your target environment:

```
docker save ansible-lifecycle-driver:2.1.0.dev0+nfviautomation -o ald.img

scp ald.img <user>@<target host>:ald.img 
```