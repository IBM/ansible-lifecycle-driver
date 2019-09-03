# Run with Python

You will need:

- Python
- Pip

## Install

Clone this repository, navigate to the root directory and install with pip:

```
pip3 install --editable .
```

Note: `--editable` is added so live code changes in the osvimdriver package are reflected in the next startup without the need for a re-install through pip.

## Configuration

To customise the configuration of the driver, create a new `ald_config.yml` in the directory you intend to run the driver from. Add the properties you desire to this file, below shows an example of some of the properties you may choose to set:

```
# Set the port the driver runs on
application:
  port: 8293

# Set the kafka address
messaging:
  connection_address: kafka:9092
```

This file will be found by the driver when it is started.

## Start Development Server

The driver can be started with the simple command:

```
ald-dev
```

## Start Production Server

To run the application in production you will need a WSGI HTTP Server. We have tested and included instructions for both Gunicorn and uWSGI (2 of the recommended options from [Flask](https://flask.palletsprojects.com/en/1.1.x/deploying/wsgi-standalone/)):

### Gunicon

Run the application by running the alm-gunicorn script:

```
ald-gunicorn
```

### uWSGI

Run the application by running the ald-uwsgi script:

```
ald-uwsgi
```

# Access Swagger UI

The Swagger UI can be found at `http://your_host:8293/api/lifecycle/ui` e.g. `http://localhost:8293/api/lifecycle/ui`
