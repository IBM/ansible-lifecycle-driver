
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
  3. The `protocol` value is user defined based on the type of request/response you intend to log. However, please note that `http` and `cmd` are known protocols in Network Automation, with suggested `protocol_metadata` attributes and a tailored user experience. See below for more details and also consult the documentation of your Network Automation installation.
  4. If `protocol` is `http`, `protocol_metadata` can have following properties:
 
     ```
     For message_type request: 
       uri - The URL of the request
       headers - Name/value pair of any relevant headers included in the request (should not include headers with sensitive data, such as `Authorization`)
       method - HTTP method of the request
     For message_type response:
       status_code - HTTP status code
       headers - Name/value pair of any relevant headers included in the response (should not include headers with sensitive data, such as `Authorization`)
     ```
     User can also add additional properties under `protocol_metadata` if required. It will vary depending on the ansible module (E.g: ansible.builtin.uri) which will be used to invoke API calls.

  5. If `protocol` is `cmd`, `protocol_metadata` can have following properties:

     ```
     For message_type request: 
       command - The command used for executing the request

     For message_type response:
       exit_code - Exit code of the command
     ```
  7. For any other protocols, `protocol_metadata` can have relevant properties which will be decided by the users.

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
        message_data: "{{ testout.content }}"
        message_type: response
        protocol: http
        protocol_metadata: 
          status_code: "{{ testout.status }}"
          response_msg: "{{ testout.msg }}"
          headers:
            Content-Type: "{{ testout.content_type }}" 

```
Before the actual task (`cp4na api call`) executes, `log api request` task is getting executed and capturing some information of `cp4na api call` task (`message_direction`, `external_request_id` etc) and also same way `log api response` captures the output data of `cp4na api call` task along with other information. Whatever parameter user sets in the `ibm_cp4na_log_message` ansible module, all are getting stored in module output result.

This output result will be useful to print the logs from ansible-driver. 

**Important :** 
1.  `ignore_errors: true` property must be added in the actual task (in the above example the actual task name is `cp4na api call` as it is calling the api with `ansible.builtin.uri`). If `ignore_errors: true` is not added and if failure occurrs in the actual task, then next task (in the example `log api response`) will not be executed and response logs will not be generated. Ansible by default does not allow to proceed with next task if failure occurs in current task.

2.  If user wants to stop the playbook in case of any error in any of the ansible task (Say, in our example - `cp4na api call` task has failed due to some api error), then `failed_when` can be used in next task (if any) after executing the response log task (In our example - `log api response` task). In the above example, after `log api response` task, if there are any other task (say, task name is `Some task`)  which user doesn't want to execute if `cp4na api call` task fails, then `failed_when: testout.status >= 400` can be added in `Some task` to stop the playbook execution. This is just an example. There are many other ways to stop the execution in Ansible.

**Sample Logs generated from 'log api request' task having 'ibm_cp4na_log_message' module:**

```
{"@timestamp": "2023-02-10T07:19:54.969Z", "@version": "1", "message": "{\"name\": \"Suryadip\", \"job\": \"Developer\"}", "HOSTNAME": "ansible-lifecycle-driver-5bc949fd76-fpc6q", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.tenantid": "1", "tracectx.processid": "4c25f422-7334-44f8-af59-7df84803b3ef", "tracectx.transactionid": "323e4b22-326a-4125-a9fa-1402eab0858f", "tracectx.taskid": "13", "message_direction": "sent", "tracectx.externalrequestid": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "content_type": "application/json", "message_type": "request", "protocol": "http", "protocol_metadata": "{\"uri\": \"https://reqres.in/api/users\", \"headers\": {\"Content-Type\": \"application/json\"}, \"method\": \"POST\"}", "tracectx.driverrequestid": "4b9c16dc-4d0d-4030-b781-72c8062dc79e"}
```
   
**Sample Logs generated from 'log api response' task having 'ibm_cp4na_log_message' module:**

```
{"@timestamp": "2023-02-10T07:19:56.302Z", "@version": "1", "message": "{\"name\": \"Suryadip\", \"job\": \"Developer\", \"id\": \"790\", \"createdAt\": \"2023-02-10T07:19:55.814Z\"}", "HOSTNAME": "ansible-lifecycle-driver-5bc949fd76-fpc6q", "path": "/usr/local/lib/python3.10/site-packages/ansibledriver/service/ansible.py", "tags": [], "type": "logstash", "thread_name": "MainThread", "level": "INFO", "logger_name": "ansibledriver.service.ansible", "tracectx.tenantid": "1", "tracectx.processid": "4c25f422-7334-44f8-af59-7df84803b3ef", "tracectx.transactionid": "323e4b22-326a-4125-a9fa-1402eab0858f", "tracectx.taskid": "13", "message_direction": "received", "tracectx.externalrequestid": "5d1cd9ca-f6d9-11ec-8084-00000a0b650b", "content_type": "application/json", "message_type": "response", "protocol": "http", "protocol_metadata": "{\"status_code\": \"201\", \"response_msg\": \"OK (87 bytes)\", \"headers\": {\"Content-Type\": \"application/json; charset=utf-8\"}}", "tracectx.driverrequestid": "4b9c16dc-4d0d-4030-b781-72c8062dc79e"}
```
