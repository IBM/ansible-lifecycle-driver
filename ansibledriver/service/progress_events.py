from ignition.service.progress_events import YAMLProgressEventLogSerializer
from ansible.parsing.yaml.dumper import AnsibleDumper
import yaml

class AnsibleYAMLProgressEventLogSerializer(YAMLProgressEventLogSerializer):

    def serialize(self, event):
        data = event.to_dict()
        # Use the Ansible dumper as it has extra representations for Ansible types, such as AnsibleUnicode
        return yaml.dump(data, Dumper=AnsibleDumper, allow_unicode=True)
