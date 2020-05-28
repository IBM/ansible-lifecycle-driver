from ignition.service.templating import ResourceTemplateContextService
from ignition.utils.propvaluemap import PropValueMap


PROPERTIES_KEY = 'properties'


class ExtendedResourceTemplateContextService(ResourceTemplateContextService):
    
    def __init__(self):
        pass

    def _configure_additional_props(self, builder, system_properties, resource_properties, request_properties, deployment_location):
        # add all resource properties under 'properties' for backwards compatibility
        properties = {}
        if isinstance(resource_properties, PropValueMap):
            for k,v in resource_properties.items_with_types():
                value_type = v.get('type')
                value = v.get('value')
                if value_type == 'key':
                    value = {
                        'keyName': v.get('keyName'),
                        'publicKey': v.get('publicKey'),
                        'privateKey': v.get('privateKey')
                    }
                properties[k] = value
        else:
            for k,v in resource_properties.items():
                properties[k] = v
        builder.add_resource_property(PROPERTIES_KEY, properties)
