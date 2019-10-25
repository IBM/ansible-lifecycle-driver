# Property Handling

## Returning properties to LM

Properties can be returned to LM by setting facts with a prefix "output__". For example, to set a property "msg":

```
- name: set fact
  set_fact:
    output__msg: "hello there!"
```

The Ansible Lifecycle Driver will recognize this as a property to be returned to LM in the response. Any number of properties can be returned in this way.

The prefix can be changed to something other than "output__" by setting the property "app.config.override.ansible.output_prop_prefix" when installing the driver using the Helm chart.
