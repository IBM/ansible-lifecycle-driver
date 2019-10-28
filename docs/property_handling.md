# Property Handling

## Lifecycle Requests

The following properties must be set in the lifecycle request "deploymentLocation.properties" only if deploymentLocation.type == 'Kubernetes':

| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| k8s-namespace      | -       | Y                                  | The K8s namespace containing the pod |
| kubeconfig_path | -    | Y                                  | The path to a kubeconfig file configured to communicate with pods. Note that this is automatically created by the Ansible Lifecycle Driver and the property is set to point to it |

The lifecycle request "deploymentLocation.type" property value determines whether Ansible Lifecycle Driver will look for an "config/inventory" or "config/inventory.k8s" Ansible inventory file in the Brent resource package:

| Deployment Location Type  | Inventory File |
| ------------------------- | -------------- |
| Kubernetes                | config/inventory.k8s |
| *                         | config/inventory     |

## Accessing LM properties in Scripts

The Ansible Lifecycle Driver supports the substitution of LM properties in Ansible scripts using [Jinja2 template variables](https://jinja.palletsprojects.com/en/2.10.x/templates/#variables). The following properties are available to Ansible scripts:

* properties: a dictionary of LM request properties.
* system_properties: a dictionary of system properties.
* dl_properties: a dictionary of deployment location properties.

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

Variable subsitution is achieved by referencing the property in a Jinja2 template, as follows (dot and square bracket notation are both supported):

```
- name: Configure Lifecycle Transition
  hosts: resource
  gather_facts: False

  vars: 
    bindIP: "{{ properties.voice_ip_address }}"
    resourceId: "{{ system_properties.resourceId }}"
  tasks:
  - name: debug
    debug:
      msg: "bindIP = {{ properties.voice_ip_address }} resourceId = {{ system_properties.resourceId }}"
```

## Returning properties to LM

Properties can be returned to LM by setting facts with a prefix "output__". For example, to set a property "msg":

```
- name: set fact
  set_fact:
    output__msg: "hello there!"
```

The Ansible Lifecycle Driver will recognize this as a property to be returned to LM in the response. Any number of properties can be returned in this way.

The prefix can be changed to something other than "output__" by setting the property "app.config.override.ansible.output_prop_prefix" when installing the driver using the Helm chart.
