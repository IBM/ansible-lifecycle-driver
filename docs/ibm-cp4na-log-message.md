
# New Custom Ansible Module for printing some specific logs

New ansible module has been written to print some specific logs in Ansible-Lifecycle-Driver before and after the actual task execution.

**Module name:**

ibm_cp4na_log_message


**Module arguments are:**

message_direction, external_request_id, content_type, message_data

(*Note - All arguments are optional*)

## Example:

**Playbook**
```
- name: uri module demo
  hosts: localhost
  become: false
  gather_facts: false
  vars:
    server: 'https://reqres.in'
    endpoint: /api/users
  tasks:
    - name: log api request
      ibm_cp4na_log_message:
        message_direction: request
        external_request_id: 5d1cd9ca-f6d9-11ec-8084-00000a0b650b
        content_type: application/json
        message_data:
          name: morpheus
          job: leader
    - name: cp4na api call
      ansible.builtin.uri:
        url: '{{ server }}{{ endpoint }}'
        method: POST
        return_content: 'yes'
        body:
          name: morpheus
          job: leader
        body_format: json
        headers:
          Content-Type: application/json
        status_code: 201
        timeout: 30
      register: testout
    - name: log api response
      ibm_cp4na_log_message:
        message_direction: response
        external_request_id: 5d1cd9ca-f6d9-11ec-8084-00000a0b650b
        content_type: application/json
        message_data: "{{ testout.json }}"

```
Before the actual task ('cp4na api call') executes, 'log api request' task is getting executed and capturing some information of 'cp4na api call' task (message_direction, external_request_id etc) and also same way 'log api response' captures the output data of 'cp4na api call' task along with other information. Whatever parameter we are setting in the ibm_cp4na_log_message module, all are getting stored in module output result.

This output result will be useful to print the logs from ansible-driver. Sample logs which is generated from ansible-driver for 'log api response' task having 'ibm_cp4na_log_message' module.
   
   {"@timestamp": "2022-06-30T09:51:36.152Z", "@version": "1",
   "**message"**: "{'name': 'morpheus', 'job': 'leader', 'id': '8',
   'createdAt': '2022-06-30T09:51:35.743Z'}", "host":
   "ansible-lifecycle-driver-575f9b5b4b-82r77", "path":
   "/usr/local/lib/python3.9/site-packages/ansibledriver/service/ansible.py",
   "tags": [], "type": "logstash", "thread_name": "MainThread", "level":
   "INFO", "logger_name": "ansibledriver.service.ansible",
   "tracectx.processid": "a553eb59-73b4-4714-8730-a96b227e0784",
   "tracectx.transactionid": "35bd5ffe-eb4a-40ed-a874-a28f95238454",
   "tracectx.taskid": "13", "**messageDirection"**: "response",
   "**tracectx.externalRequestId"**: "5d1cd9ca-f6d9-11ec-8084-00000a0b650b",
   "**ContentType"**: "application/json"}
