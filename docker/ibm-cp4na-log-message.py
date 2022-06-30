#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# This custom module is for printing some specified logs

from ansible.module_utils.basic import AnsibleModule
import requests

def run_module():
    # defining available arguments/parameters a user can pass to the module
    module_args = dict(
        message_direction=dict(type='str'),
        external_request_id=dict(type='str'),
        content_type=dict(type='str'),
        message_data=dict(type='str')
    )

    result = dict()

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    message_direction = module.params['message_direction']
    external_request_id = module.params['external_request_id'] 
    content_type = module.params['content_type']
    message_data = module.params['message_data']

    result['message_direction'] = message_direction
    result['external_request_id'] = external_request_id
    result['content_type'] = content_type
    result['message_data'] = message_data

    module.exit_json(**result)


def main():
    run_module()
    
if __name__ == '__main__':
    main()
