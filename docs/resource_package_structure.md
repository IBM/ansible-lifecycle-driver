# Resource Package Structure for Ansible Lifecycle Driver

The Brent resource package contains Ansible inventory configuration and scripts used by the Ansible Lifecycle Driver. The structure of the directory within the package is defined by the driver. Under this top level directory the driver expects the following directory structure:

```
config
  inventory
scripts
  *.yaml
```

The config directory contains [Ansible inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) related configuration files. This driver's [Ansible Inventory Guide](./ansible_inventory.md) describes how to construct these files.

The scripts directory contains your Ansible scripts. The naming must reflect the naming of the lifcycle and operation scripts defined in your LM resource.yaml file; the naming is case-sensitive and it supports only two formats i.e lower case or camel case but the extension can be either 'yml' or 'yaml'. Ancillary files can be added under the scripts directory and these will be included in the payload to the Ansible Lifecycle Driver.

For example, the formats supported for `Configure` transition are as follows.

`configure.yml` or `Configure.yml` or `configure.yaml` or `Configure.yaml`


## Idempotency

The Ansible Lifecycle Driver cannot guarantee that scripts will not be run more than once; for this reason, Ansible scripts should be [idempotent (that is, it should be possible to run them repeatedly, without any intervening actions)](https://docs.ansible.com/ansible/latest/reference_appendices/glossary.html).