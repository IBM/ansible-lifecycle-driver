
# New Custom Ansible Module for printing some specific logs

New ansible module has been written to print some specific logs in Ansible-Lifecycle-Driver before and after the actual task execution.

**Module name:**

ibm_cp4na_log_message


**Module arguments:**

The module will accept the following parameters:

| Name | Type | Description | Required |
| --- | --- | --- | --- | 
| message_direction | str | the `message_direction` to be included in the logs | Yes |
| message_type | str | the `message_type` to be included in the logs | Yes |
| message_data | str | the `message_data` to be included in the logs | No |
| content_type | str | the `content_type` to be included in the logs | Yes if `message_data` is provided |
| protocol | str | the `protocol` to be included in the logs | Yes |
| protocol_metadata | dict | the `protocol_metadata` to be included in the logs (will be formatted as a JSON string by the module/driver) | No |
| external_request_id | String | the `tracectx.externalrequestid` to be included in the logs | Yes | 

**Note**: supported values for `message_direction` is : `sent` or `received`

## Example:

**Playbook**
```
---
- name: log module demo
  hosts: localhost
  become: false
  gather_facts: False
  vars:
    server: "https://reqres.in"
    endpoint: "/api/users"
  tasks:
    - name: log api request
      ibm_cp4na_log_message:
        message_direction: sent
        external_request_id: 5d1cd9ca-f6d9-11ec-8084-00000a0b650b
        content_type: application/json
        message_data: {"name": "Suryadip", "job": "Developer"}
        message_type: sample_type
        protocol: http
        protocol_metadata: 
          url: "{{ server }}{{ endpoint }}"

    - name: cp4na api call
      ansible.builtin.uri:
        url: "{{ server }}{{ endpoint }}"
        method: POST
        return_content: yes
        body: {"name": "Suryadip", "job": "Developer"}
        body_format: json
        headers:
          Content-Type: application/json
        status_code: 201
        timeout: 30
      register: testout

    - name: log api response
      ibm_cp4na_log_message:
        message_direction: sent
        external_request_id: 5d1cd9ca-f6d9-11ec-8084-00000a0b650b
        content_type: application/json
        message_data: "{{ testout.json }}"
        message_type: sample_type
        protocol: http

```
Before the actual task ('cp4na api call') executes, 'log api request' task is getting executed and capturing some information of 'cp4na api call' task (message_direction, external_request_id etc) and also same way 'log api response' captures the output data of 'cp4na api call' task along with other information. Whatever parameter we are setting in the ibm_cp4na_log_message module, all are getting stored in module output result.

This output result will be useful to print the logs from ansible-driver. Sample logs which is generated from ansible-driver for 'log api request' task having 'ibm_cp4na_log_message' module.
   
{"@timestamp": "2022-07-14T11:52:59.063Z", "@version": "1", "**message**": "{'name': 'Suryadip', 'job': 'Developer'}", "host": "ansible-lifecycle-driver-57bbbc5dd9-9wmtr", "path": "/usr/local/lib/python3.9/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.processid": "36927a71-c901-46d3-8d6a-dccafbac88bf", "tracectx.transactionid": "31f4ec1f-6830-481a-9df0-b3b5f47dd26e", "tracectx.taskid": "13", "**message_direction**": "sent", "**tracectx.externalrequestid**": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "**content_type**": "application/json", "**message_type**": "sample_type", "**protocol**": "http", "**protocol_metadata**": {"url": "https://reqres.in/api/users"}, "**tracectx.driverrequestid**": "05f7ce14-9988-47ae-af44-2e6f15bc3231"}
