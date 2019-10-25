# Resource Package Structure for Ansible Lifecycle Driver

The Ansible Lifecycle Driver expects a specific structure in the Brent resource package under the 'Lifecycle/ansible' directory, as follows:

```
config
  inventory
  inventory.k8s
scripts
  *.yaml
```

The config directory contains [Ansible inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) related configuration files. [Ansible Inventory](./ansible_inventory.md) describes how to construct these files.

The scripts directory contains your Ansible scripts. The naming must reflect the naming of the lifcycle and operation scripts defined in your LM resource.yaml file; the naming is case-sensitive but the extension can be either 'yml' or 'yaml'. Ancillary files can be added under the scripts directory and these will be included in the payload to the Ansible Lifecycle Driver.
