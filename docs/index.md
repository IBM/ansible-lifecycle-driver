# Ansible Lifecycle Driver

This driver implements the [IBM Telco Network Cloud Manager - Orchestration](https://www.ibm.com/support/knowledgecenter/SSDSDC_1.3/welcome_page/kc_welcome-444.html) Brent Lifecycle APIs.

This driver uses Ansible v9.5.1 which may have an impact on your playbooks. See the [porting](porting-playbooks.md) guide for more details.

Please read the following guides to get started with the Ansible Lifecycle Driver.

## Install

- [Kubernetes Install](./install_with_helm.md) - install the driver to Kubernetes using Helm

## Using the Driver

- [Resource Package Structure for Ansible Lifecycle Driver](./resource_package_structure.md) - details on the expected Ansible Lifecycle Driver specific parts of the Brent resource package.
- [Ansible Inventory](./ansible_inventory.md) - details on Ansible inventory files and variable substitution.
- [Property Handling](./property_handling.md) - details on property handling, in particular how properties are returned back to LM.
- [Resource Transition Progress Events](./progress_events.md) - details of events logged during Ansible playbook execution
- [Porting from Ansible 4.2 ](./porting-playbooks.md) - port playbooks from Ansible 4.2 to 9.5.1
- [Enabling logs for Ansible driver](./ibm-cp4na-log-message.md) - New custom ansible module for printing specific logs.