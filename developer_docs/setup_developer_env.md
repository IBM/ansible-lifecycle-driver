# Setup Developer Environment

To develop the Ansible Lifecycle Driver you need Python v3.6.9+ (install using instructions suitable for your operating system).

## Pip/Setup

Once installed, make sure you have the latest `pip`, `setuptools` and `wheel`:

```
python3 -m pip install -U pip setuptools wheel
```

It's also recommended that you create a [virtualenv](https://virtualenv.pypa.io/en/latest/) to manage an isolated Python env for this project:

Install virtualenv:

```
python3 -m pip install virtualenv
```

## Virtualenv

Create a virtualenv (do this from the root of your project clone):

```
python3 -m virtualenv env
```

The virtualenv should be activated in your terminal when working on the driver:

(Unix/Mac)
```
source env/bin/activate
```

(Windows Powershell)
```
Scripts\activate.ps1
```

(Windows Other)
```
Scripts\activate
```

## Install Ignition

You may need a development version of [Ignition](https://github.com/IBM/ignition), (check `ansibledriver/pkg_info.json`. If `ignition-version` includes a `.devX` version then you do). You should install the development version of Ignition into your environment before installing the driver.

Clone the [Ignition](https://github.com/IBM/ignition) project and install it into your virtualenv:

```
python3 -m pip install --editable ~/my-git-repos/ignition
```

## Install Driver Libraries

You should install the driver to make it's modules available for import. This is required to run the unit tests.

```
python3 -m pip install --editable . 
```

Use the `--editable` flag to avoid re-installing on every change you make. 


## Build Driver Whl

To build the driver for distribution you need to build a whl:

```
python3 setup.py bdist_wheel
```

The `.whl` file will be created in the `dist` directory at the root of the project. This `.whl` file can be transferred and used to install this driver with pip elsewhere and/or to create a docker image.

## Build Docker Image

First, you need to build a `.whl` as shown above.

Then copy the whl to the `docker/whls` directory:

```
cp dist/ansible_lifecycle_driver-<version number>-py3-none-any.whl docker/whls/
```

> Note: make sure you don't have any old `whls` in that directory

If you have been using a custom/development version of Ignition, you will need to include the whl for that also:

```
cp ~/my-git-repos/ignition/dist/ignition_framework-2.0.4.dev0-py3-none-any.whl docker/whls/
```

Build the image with the docker CLI:

```
docker build -t ansible-lifecycle-driver:dev .
```