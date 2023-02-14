#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# This custom module is for printing some specified logs

from ansible.module_utils.basic import AnsibleModule

def run_module():
    # defining available arguments/parameters a user can pass to the module
    module_args = dict(
        message_direction=dict(type='str', required=True, choices=['sent', 'received']),
        external_request_id=dict(type='str', required=True),
        message_data=dict(type='str'),
        message_type=dict(type='str', required=True, choices=['request', 'response', 'message']),
        content_type=dict(type='str'),
        protocol=dict(type='str', required=True),
        protocol_metadata=dict(type='dict', default={})
    )

    result = dict()

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_together=[['message_data', 'content_type']]
    )

    if(module.check_mode):
        module.exit_json(**result)

    message_direction = module.params['message_direction']
    external_request_id = module.params['external_request_id'] 
    message_data = module.params['message_data']
    message_type = module.params['message_type']
    content_type = module.params['content_type']
    protocol = module.params['protocol']
    protocol_metadata = module.params['protocol_metadata']

    if(protocol is None):
        module.fail_json("Please provide a non empty protocol")
    if(external_request_id is None):
        module.fail_json("Please provide a non empty external_request_id")

    result['message_direction'] = message_direction
    result['external_request_id'] = external_request_id
    result['message_data'] = message_data
    result['message_type'] = message_type
    result['content_type'] = content_type
    result['protocol'] = protocol
    result['protocol_metadata'] = protocol_metadata

    module.exit_json(**result)


def main():
    run_module()
    
if __name__ == '__main__':
    main()
