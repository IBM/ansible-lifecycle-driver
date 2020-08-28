# Building Image with Extra Modules

Often additional Python or Ansible libraries are required in your playbooks. Usually, you would install them to your Ansible controller. 

In the case of the driver, the controller is the docker container running the driver application, so it is not easy to install additional libraries.

Long term - we'd like a way to dynamically add libraries to the driver, potentially with isolated environments so 2 Resources requiring different versions of the same library can co-exist.

Short term - we can build a custom image for the Ansible driver with libraries pre-installed, this guide shows you how.

# Add Libraries

Navigate to the `docker` repo of this repository, to find the source files for the Docker image. 

```
cd docker
```

There are 4 types of libraries you can add:

1. Ansible modules
2. Ansible roles
3. Ansible module utils
4. Python libraries

To add Ansible modules, copy the `.py` for each module into the `library` directory:

```
cp path/to/my/modules/*.py library/
```

To add Ansible roles, copy them to the `roles` directory (ensure you copy the entire directory for the role, including the top level directory which have the desired name of the role): 

```
# Repeat for each role
cp -r path/to/my/role roles/
```

To add Ansible module utils, copy the `.py` for each into the `library` directory:

```
cp path/to/my/module_utils/*.py library/
```

To add Python libraries, add entires for them into the `extra-requirements.txt` file:

```
hpOneView==5.3.0
```

> Ideally, include a version range or explicit version

## Example

The HP OneView module will act as our example, it can be added by first cloning the repo:

```
git clone https://github.com/HewlettPackard/oneview-ansible.git
```

This repository includes Ansible modules (in `library`) and module-utils (in `library/module-utils`), so the following commands were run:

```
cp -r oneview-ansible/library/*.py library/

cp -r oneview-ansible/library/module_utils/*.py module_utils
```

In addition, the repo has a `requirements.txt` file which indicates the Python libraries it requires. These were added to the `extra-requirements.txt` (copy and paste):

> Exclude `ansible`

```
hpICsp
hpOneView==5.3.0
```

Lastly, the HP OneView repo clone was removed:

```
rm -rf oneview-ansible
```

# Build the Image

To build the image, you must first build the `.whl` file for the application. 

Go back one directory, clear out any existing builds, then execute the setup command: 

```
cd ../
rm -rf ./build
rm -rf ./dist

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

You can now build the docker image. You should give the image and appropriate version number so you can manage multiple versions as you make further changes. It is recommended to use the following format:

`<release_version_number>+<my_label>`

Where:

- `<release_version_number>` is the version number from the `.whl` file. For example, with a whl called `ansible_lifecycle_driver-2.1.0.dev0-py3-none-any.whl` use `2.1.0.dev0`
- `<my_label>` is a label of your choosing which indicates the customisations you have made e.g. `issue69` to indicate it's related to an issue or `hponeview` to indicate it's a version that include HP OneView modules.

> Ensure `<release version number>` matches the value on the `.whl` file. E.g. `2.1.0.dev0`

```
docker build -t ansible-lifecycle-driver:<release_version_number>+<my_label> .
```

**NOTE:** If you do not choose a sensible version number for the image you may make it very difficult to get support from the development teams, as they will not be able to identify the version of the code you have

The image can now be copied to your target Kubernetes environment:

```
docker save ansible-lifecycle-driver:<release_version_number>+<my_label> -o ald.img

scp ald.img <user>@<target host>:ald.img 
```

On your target Kubernetes environment load the image into the docker environment:

```
docker load -i ald.img
```

Tag and load it into a docker registry if required.

Update your Ansible driver deployment to use this image, either:

At install time:

```
helm install ansiblelifecycledriver-<version>.tgz --name ansible-lifecycle-driver --set docker.image=ansible-lifecycle-driver --set docker.version=<release_version_number>+<my_label>
```

Or post-installation:

```
kubectl edit deployment ansible-lifecycle-driver
```

Find the `image:` value and update it to the value of your new image.