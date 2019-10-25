# Property Handling

## Lifecycle Requests

The following properties must be set in the lifecycle request "deploymentLocation.properties":

| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| k8s-namespace      | -       | Y                                  | The K8s namespace containing the pod |
| kubeconfig_path | -    | Y                                  | The path to a kubeconfig file configured to communicate with pods. Note that this is automatically created by the Ansible Lifecycle Driver and the property is set to point to it |

The lifecycle request "deploymentLocation.type" property value determines whether Ansible Lifecycle Driver will look for an "inventory"

Kubernetes

## Returning properties to LM

Properties can be returned to LM by setting facts with a prefix "output__". For example, to set a property "msg":

```
- name: set fact
  set_fact:
    output__msg: "hello there!"
```

The Ansible Lifecycle Driver will recognize this as a property to be returned to LM in the response. Any number of properties can be returned in this way.

The prefix can be changed to something other than "output__" by setting the property "app.config.override.ansible.output_prop_prefix" when installing the driver using the Helm chart.
