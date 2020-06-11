# Property Handling

## Accessing LM properties in Scripts (variable substitution)

The Ansible Lifecycle Driver supports the substitution of LM properties in all files under the `ansible` directory, using [Jinja2 template variables](https://jinja.palletsprojects.com/en/2.10.x/templates/#variables). The following properties are available:

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

Variable substitution is achieved by referencing the property in a Jinja2 template, as follows (dot and square bracket notation are both supported):

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
      msg: "bindIP = {{ voice_ip_address }} resourceId = {{ system_properties.resourceId }}"
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
