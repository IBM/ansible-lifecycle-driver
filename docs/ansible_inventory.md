# Ansible Inventory Files

## Brent Resource Package

The "config" subdirectory in the Brent resource package driver root directory contains Ansible inventory and ancillary configuration files. The Ansible Driver will look for an Ansible inventory file in the config directory as follows:

* it will first look for an inventory file named `inventory.[infrastructure_type]`, where `[infrastructure_type]` is replaced with the deployment location (infrastructure) type. For example, if the deployment location type is `Kubernetes`, it will look for an inventory file called `inventory.Kubernetes`.
* if if doesn't find an inventory file at this location, it will default to an inventory file named `inventory`. For backwards compatibility, if the deployment location (infrastructure) type is `Kubernetes`, the driver will first look for an inventory file named `inventory.k8s`.
* if no `inventory` file is found, the driver will construct an inventory file for the request (which will be removed after processing the request). The inventory file will look like this:

  ```
  [run_hosts]
  localhost ansible_connection=local ansible_python_interpreter="/usr/bin/env python3" host_key_checking=False
  ```

Note: if you wish to split your inventory out into separate host variable files then you may do so. For example:

```
config
  host_vars
    host1.yml
  inventory
```

## Variable Substitution

The Ansible Lifecycle Driver supports the substitution of LM properties in inventory files under the "config" directory, using [Jinja2 template variables](https://jinja.palletsprojects.com/en/2.10.x/templates/#variables). The following properties are available:

* properties: a dictionary of LM request properties (these can also be accessed without the `properties.` prefix).
* system_properties: a dictionary of system properties.
* deployment_location.properties: a dictionary of deployment location properties.

The system properties comprise the following:

| Property Name  | Description |
| ------------------------- | -------------- |
| resourceId                | The LM resource instance id |
| requestId                         | The LM orchestration request ID     |
| metricKey                         | The LM resource metric key (if set)     |
| resourceManagerId                         | The LM resource manager id     |
| deploymentLocation                         | The name of the LM deployment location name in which the resource instance resides    |
| resourceType                         | The resource instance type |

In addition, any LM orchestration request context properties are added in here.

For example, the following inventory file substitutes the LM property "mgmt_ip_address" for "ansible_host":

```
---
ansible_user: ubuntu
ansible_host: {{ mgmt_ip_address }}
ansible_ssh_pass: ubuntu
ansible_connection: ssh
ansible_become_pass: ubuntu
ansible_sudo_pass: ubuntu
```

Note that both square brackets and dot notation are supported during property substitution. For example, `properties['prop1']` and `properties.prop1` are equivalent.

## Support for SSH and K8s Connections

The Ansible Lifecycle Driver supports inventory for SSH and K8s connections, as described in the introduction.

## SSH Connections

An example SSH inventory file (which must be located in the Brent resource package at ansible/config/inventory):

```
---
ansible_user: ubuntu
ansible_host: {{ mgmt_ip_address }}
ansible_ssh_pass: ubuntu
ansible_connection: ssh
ansible_become_pass: ubuntu
ansible_sudo_pass: ubuntu
```

In this example, the ansible_host is set to an LM property value.

## K8s Connections

It is possible to use the [Kubectl Ansible connection plugin](https://docs.ansible.com/ansible/2.7/plugins/connection/kubectl.html) (as opposed to the default SSH connection plugin) to communicate with pods. For this to work, the deployment location properties must set the property `connection_type` to `kubectl` i.e. `deployment_location.properties == 'kubectl'` (see the [Kubernetes Driver documentation](https://github.com/accanto-systems/kubernetes-driver/blob/master/docs/user-guide/deployment-locations.md) for a description of the Kubernetes deployment location properties synatx). This will switch the Ansible driver to use kubectl to communicate with pods for the lifecycle transition request. An example inventory file showing this is:

```
---
ansible_connection: kubectl
ansible_kubectl_pod: {{ podName }}
ansible_kubectl_namespace: {{ deployment_location.properties['k8s-namespace'] }}
ansible_kubectl_kubeconfig: {{ deployment_location.properties.kubeconfig_path }}
```

The inventory must also set `ansible_connection` to `kubectl`. `podName` is an LM property with a value set to the pod name of the pod that the driver will connect to. The `deployment_location.properties.kubeconfig_path` property holds the path of a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) that the kubectl connection plugin will use to communicate with the pod (constructed from the deployment location properties by the driver during request execution).

## Using a Jumphost in Inventory

It is often necessary to use a [Jumphost](https://docs.ansible.com/ansible/latest/reference_appendices/faq.html#how-do-i-configure-a-jump-host-to-access-servers-that-i-have-no-direct-access-to) to access a VM using SSH. It is possible to do this with the Ansible Lifecycle Driver using an inventory like this:

```
---
ansible_user: ubuntu
ansible_host: {{ mgmt_ip_address }}
ansible_ssh_pass: ubuntu
ansible_connection: ssh
ansible_become_pass: ubuntu
ansible_sudo_pass: ubuntu
ssh_with_jumphost: "-o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no -o ProxyCommand='sshpass -p {{ jumphost_password }} ssh -o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no -W %h:%p {{ jumphost_username }}@{{ jumphost_ip }}'"
ssh_without_jumphost: "-o 'UserKnownHostsFile=/dev/null' -o StrictHostKeyChecking=no"
ansible_ssh_common_args: "{{ ssh_with_jumphost if jumphost_ip is defined else ssh_without_jumphost }}"
```

If the LM properties have defined a "jumphost_ip" property this configuration will construct "ansible_ssh_common_args" using ProxyCommand to proxy the SSH connection through the jumphost, using jumphost properties from the LM request. If not, a standard direct SSH connection is configured.