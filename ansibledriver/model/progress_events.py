from ignition.model.progress_events import ResourceTransitionProgressEvent
from collections import OrderedDict

class AnsibleEvent(ResourceTransitionProgressEvent):
    
    def _convert_result_to_log_safe_dict(self, task_result):
        return {
            'msg': task_result.get('msg', None),
            'changed': task_result.get('changed', None),
            'failed': task_result.get('failed', None),
            'skipped': task_result.get('skipped', None),
            'rc': task_result.get('rc', None),
            'results': [self._convert_result_to_log_safe_dict(r) for r in task_result.get('results', [])]
        }


class PlaybookResultEvent(AnsibleEvent):
    """
    To report the stats of a playbook execution
    """
    progress_event_type = 'ansible/PlaybookResult'

    def __init__(self, plays, host_stats):
        super().__init__()
        self.plays = plays
        self.host_stats = host_stats

    def _details(self):
        return  {
            'plays': self.plays,
            'hostStats': self.host_stats
        }

class PlayMatchedNoNoHostsEvent(AnsibleEvent):
    """
    Indicates a play had no matching hosts so did not execute
    """
    progress_event_type = 'ansible/PlayMatchedNoNoHostsEvent'

    def __init__(self, play_name):
        super().__init__()
        self.play_name = play_name
    
    def _details(self):
        return  {
            'playName': self.play_name
        }

class PlayStartedEvent(AnsibleEvent):
    """
    Indicates a play, within a playbook, has started
    """

    progress_event_type = 'ansible/PlayStarted'

    def __init__(self, play_name):
        super().__init__()
        self.play_name = play_name

    def _details(self):
        return  {
            'playName': self.play_name
        }

class TaskStartedEvent(AnsibleEvent):
    """
    Indicates a task, within a play, has started. The task may be executed on multiple hosts but this event will only be emitted once
    """

    progress_event_type = 'ansible/TaskStarted'

    def __init__(self, task_name, args=None, args_hidden=False):
        super().__init__()
        self.task_name = task_name
        self.args = args or {}
        self.args_hidden = args_hidden

    def _details(self):
        return  {
            'taskName': self.task_name,
            'args': self.args,
            'argsHidden': self.args_hidden
        }

class TaskStartedOnHostEvent(AnsibleEvent):
    """
    Indicates a task, within a play, has started on a particular host
    Note: only used in v2.8+ of Ansible
    """

    progress_event_type = 'ansible/TaskStartedOnHost'

    def __init__(self, task_name, host_name, args=None, args_hidden=False):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.args = args or {}
        self.args_hidden = args_hidden

    def _details(self):
        return  {
            'taskName': self.task_name,
            'hostName': self.host_name,
            'args': self.args,
            'argsHidden': self.args_hidden
        }

class TaskCompletedOnHostEvent(AnsibleEvent):
    """
    Indicates a task completed successfully. One event should be created for each host the task is executed on 
    """
    progress_event_type = 'ansible/TaskCompletedOnHost'

    def __init__(self, task_name, host_name, task_result, item_label=None, delegated_host_name=None):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.delegated_host_name = delegated_host_name
        self.task_result = task_result
        self.item_label = item_label
    
    def _details(self):
        return  {
            'taskName': self.task_name,
            'itemLabel': self.item_label,
            'hostName': self.host_name,
            'delegatedHostName': self.delegated_host_name,
            'taskResult': self._convert_result_to_log_safe_dict(self.task_result)
        }

class TaskRetryOnHostEvent(AnsibleEvent):
    """
    Indicates a task is being retried (using "retries" and "until" on a task in a playbook). One event will be created for each retry
    Note: if using "with_items" or any other loop, then an event will be created for each retry for each item however it's not possible to get hold of the item label 
    """
    progress_event_type = 'ansible/TaskRetryOnHost'

    def __init__(self, task_name, host_name, task_result, delegated_host_name=None):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.delegated_host_name = delegated_host_name
        self.task_result = task_result
    
    def _details(self):
        return  {
            'taskName': self.task_name,
            'hostName': self.host_name,
            'delegatedHostName': self.delegated_host_name,
            'taskResult': self._convert_result_to_log_safe_dict(self.task_result)
        }

class TaskFailedOnHostEvent(AnsibleEvent):
    """
    Indicates a task failed. One event should be created for each host the task fails on
    """
    progress_event_type = 'ansible/TaskFailedOnHost'

    def __init__(self, task_name, host_name, task_result, item_label=None, delegated_host_name=None):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.delegated_host_name = delegated_host_name
        self.task_result = task_result
        self.item_label = item_label

    def _details(self):
        return  {
            'taskName': self.task_name,
            'itemLabel': self.item_label,
            'hostName': self.host_name,
            'delegatedHostName': self.delegated_host_name,
            'taskResult': self._convert_result_to_log_safe_dict(self.task_result)
        }

class TaskSkippedOnHostEvent(AnsibleEvent):
    """
    Indicates a task was skipped. One event should be created for each host the task skips on
    """
    progress_event_type = 'ansible/TaskSkippedOnHost'

    def __init__(self, task_name, host_name, task_result, item_label=None, delegated_host_name=None):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.delegated_host_name = delegated_host_name
        self.task_result = task_result
        self.item_label = item_label

    def _details(self):
        return  {
            'taskName': self.task_name,
            'itemLabel': self.item_label,
            'hostName': self.host_name,
            'delegatedHostName': self.delegated_host_name,
            'taskResult': self._convert_result_to_log_safe_dict(self.task_result)
        }

class HostUnreachableEvent(AnsibleEvent):
    """
    Indicates a host was unreachable when trying to execute a task
    """
    progress_event_type = 'ansible/HostUnreachable'

    def __init__(self, task_name, host_name, task_result, delegated_host_name=None):
        super().__init__()
        self.task_name = task_name
        self.host_name = host_name
        self.delegated_host_name = delegated_host_name
        self.task_result = task_result
    
    def _details(self):
        return  {
            'taskName': self.task_name,
            'hostName': self.host_name,
            'delegatedHostName': self.delegated_host_name,
            'taskResult': self._convert_result_to_log_safe_dict(self.task_result)
        }

class VarPromptEvent(AnsibleEvent):
    """
    Indicates there was an attempt to prompt for a var (which the driver won't be able to handle)
    """
    progress_event_type = 'ansible/VarPrompt'

    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name
    
    def _details(self):
        return  {
            'varName': self.var_name
        }
