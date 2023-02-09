
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
| message_data | str | the `message` to be included in the logs | No |
| content_type | str | the `content_type` to be included in the logs | Yes if `message_data` is provided |
| protocol | str | the `protocol` to be included in the logs | Yes |
| protocol_metadata | dict | the `protocol_metadata` to be included in the logs (will be formatted as a JSON string by the module/driver) | No |
| external_request_id | String | the `tracectx.externalrequestid` to be included in the logs | Yes | 

**Notes**: 
  1. Supported values for `message_direction` are : `sent` and `received`.
  2. Supported values for `message_type` are : `request`, `response` and `message`.
  3. Supported values for `protocol` are : `http`, `cmd` or any other protocols.
  4. If `protocol` is `http`, `protocol_metadata` can have following properties:
 
     ```
     For message_type request: 
       uri - The URL of the request
       headers - Name/value pair of any relevant headers included in the request (should not include headers with sensitive data, such as `Authorization`)
       method - HTTP method of the request
     For message_type response:
       status_code - HTTP status code
       status_reason_phrase - HTTP status meaning, if provided (e.g. 200 OK)
       headers - Name/value pair of any relevant headers included in the response (should not include headers with sensitive data, such as `Authorization`)
     ```
  5. If `protocol` is `cmd`, `protocol_metadata` can have following properties:

     ```
     For message_type request: 
       command - The command used for executing the request

     For message_type response:
       exit_code - Exit code of the command
     ```
  6. If `message_type` is message, then `protocol_metadata` values will be decided by users.
  7. For any other `protocols`, `protocol_metadata` can have relevant properties.

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
          headers:
            Content-Type: application/json
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
      ignore_errors: true

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
          status_reason_phrase: "{{ testout.msg }}"
          headers:
            Content-Type: "{{ testout.content_type }}" 

```
Before the actual task (`cp4na api call`) executes, `log api request` task is getting executed and capturing some information of `cp4na api call` task (`message_direction`, `external_request_id` etc) and also same way `log api response` captures the output data of `cp4na api call` task along with other information. Whatever parameter we are setting in the `ibm_cp4na_log_message` module, all are getting stored in module output result.

This output result will be useful to print the logs from ansible-driver. 

**Important :** We need to add `ignore_errors: true` mandatorily in the actual task (in the above example the actual task name is `cp4na api call` as it is calling the api with `ansible.builtin.uri`). If we do not add `ignore_errors: true` and if failure occurrs in the actual task, then next task (in the example `log api response`) will not be executed and we will not be able to get the response logs. Ansible by default does not allow to proceed with next task if failure occurs in current task so we need to use `ignore_errors: true`.

**Sample Logs generated from 'log api request' task having 'ibm_cp4na_log_message' module:**

{"@timestamp": "2023-02-01T11:02:34.279Z", "@version": "1", "**message**": "{'name': 'Suryadip', 'job': 'Developer'}", "HOSTNAME": "ansible-lifecycle-driver-8654574df5-r4pt2", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.processid": "9b6188ac-6ced-4e4f-91b7-0a10c021337e", "tracectx.transactionid": "b7ef1310-4543-4640-959e-c54277b1f13f", "tracectx.taskid": "13", "**message_direction**": "sent", "**tracectx.externalrequestid**": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "**content_type**": "application/json", "**message_type**": "request", "**protocol**": "http", "**protocol_metadata**": {"uri": "https://reqres.in/api/users", "headers": {"Content-Type": "application/json"}, "method": "POST"}, "**tracectx.driverrequestid**": "d74c6bd0-8c09-48e6-b59d-fe8603a61424"}
   
**Sample Logs generated from 'log api response' task having 'ibm_cp4na_log_message' module:**

{"@timestamp": "2023-02-01T11:02:35.600Z", "@version": "1", "**message**": "{'name': 'Suryadip', 'job': 'Developer', 'id': '168', 'createdAt': '2023-02-01T11:02:35.035Z'}", "HOSTNAME": "ansible-lifecycle-driver-8654574df5-r4pt2", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.processid": "9b6188ac-6ced-4e4f-91b7-0a10c021337e", "tracectx.transactionid": "b7ef1310-4543-4640-959e-c54277b1f13f", "tracectx.taskid": "13", "**message_direction**": "received", "**tracectx.externalrequestid**": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "**content_type**": "application/json", "**message_type**": "response", "**protocol**": "http", "**protocol_metadata**": {"status_code": "201", "status_reason_phrase": "OK (87 bytes)", "headers": {"Content-Type": "application/json; charset=utf-8"}}, "**tracectx.driverrequestid**": "d74c6bd0-8c09-48e6-b59d-fe8603a61424"}
