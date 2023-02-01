
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
        message_type: request
        protocol: http
        protocol_metadata: 
          uri: "{{ server }}{{ endpoint }}"
          method: POST

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
        message_direction: received
        external_request_id: 5d1cd9ca-f6d9-11ec-8084-00000a0b650b
        content_type: application/json
        message_data: "{{ testout.json }}"
        message_type: response
        protocol: http
        protocol_metadata: 
          status_code: "{{ testout.status }}"

```
Before the actual task ('cp4na api call') executes, 'log api request' task is getting executed and capturing some information of 'cp4na api call' task (message_direction, external_request_id etc) and also same way 'log api response' captures the output data of 'cp4na api call' task along with other information. Whatever parameter we are setting in the ibm_cp4na_log_message module, all are getting stored in module output result.

This output result will be useful to print the logs from ansible-driver. Sample logs which are generated from ansible-driver are mentioned below :

**Logs generated from 'log api request' task having 'ibm_cp4na_log_message' module:**

{"@timestamp": "2023-02-01T07:38:05.660Z", "@version": "1", "**message**": "{'name': 'Suryadip', 'job': 'Developer'}", "HOSTNAME": "ansible-lifecycle-driver-8654574df5-r4pt2", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.processid": "0bfb6dad-b188-46ec-8f57-93a9e40f9d83", "tracectx.transactionid": "2221c99d-a414-496e-b794-0ccfac9cfcda", "tracectx.taskid": "13", "**message_direction**": "sent", "**tracectx.externalrequestid**": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "**content_type**": "application/json", "**message_type**": "request", "**protocol**": "http", "**protocol_metadata**": {"uri": "https://reqres.in/api/users", "method": "POST"}, "**tracectx.driverrequestid**": "273bf22d-9ffe-4a6d-b483-51c4c0186da3"}
   
**Logs generated from 'log api response' task having 'ibm_cp4na_log_message' module:**

{"@timestamp": "2023-02-01T07:38:06.894Z", "@version": "1", "**message**": "{'name': 'Suryadip', 'job': 'Developer', 'id': '727', 'createdAt': '2023-02-01T07:38:06.449Z'}", "HOSTNAME": "ansible-lifecycle-driver-8654574df5-r4pt2", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.processid": "0bfb6dad-b188-46ec-8f57-93a9e40f9d83", "tracectx.transactionid": "2221c99d-a414-496e-b794-0ccfac9cfcda", "tracectx.taskid": "13", "**message_direction**": "received", "**tracectx.externalrequestid**": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "**content_type**": "application/json", "**message_type**": "response", "**protocol**": "http", "**protocol_metadata**": {"status_code": "201"}, "**tracectx.driverrequestid**": "273bf22d-9ffe-4a6d-b483-51c4c0186da3"}

**Note**: We can pass any releavant data in protocol_metadata filed in this new ansible module. In this example, inside protocol_metadata, we have given uri & method in log api request task and for log api response task, we have given status_code. So we will be able to see those data in logs. We can also give status_reason_phrase inside protocol_metadata in log api response task. It is totally depends on user.
