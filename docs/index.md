# Ansible Lifecycle Driver

This driver implements the [Stratoss&trade; Lifecycle Manager](http://servicelifecyclemanager.com/2.1.0/) Brent Lifecycle APIs.

Please read the following guides to get started with the Ansible Lifecycle Driver

## Install

- [Kubernetes Install](./install_with_helm.md) - install the driver to Kubernetes using Helm

## Using the Driver

- [Resource Package Structure for Ansible Lifecycle Driver](./resource_package_structure.md) - details on the expected Ansible Lifecycle Driver specific parts of the Brent resource package.
- [Ansible Inventory](./ansible_inventory.md) - details on Ansible inventory files and variable substitution.
- [Property Handling](./property_handling.md) - details on property handling, in particular how properties are returned back to LM.
- [Resource Transition Progress Events](./progress_events.md) - details of events logged during Ansible playbook execution