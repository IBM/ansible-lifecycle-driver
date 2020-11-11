# Resource Transition Progress Events

During the execution of playbooks the following events are logged as Resource transition progress events.

| Event | Description |
| --- | --- |
| PlayStartedEvent | Indicates a play, within a playbook, has started |
| PlayMatchedNoNoHostsEvent | Indicates a play had no matching hosts so did not execute |
| TaskStartedEvent | Indicates a task, within a play, has started. The task may be executed on multiple hosts but this event will only be omitted once |
| TaskStartedOnHostEvent | Indicates a task, within a play, has started on a particular host Note: only omitted when this driver upgrades to v2.8+ of Ansible (currently v2.7) | 
| TaskCompletedOnHostEvent | Indicates a task completed successfully. One event should be created for each host the task is executed on |
| TaskRetryOnHostEvent | Indicates a task is being retried (using "retries" and "until" on a task in a playbook). One event will be created for each retry. Note: if using "with_items" or any other loop, then an event will be created for each retry for each item however it's not possible to get hold of the item label |
| TaskFailedOnHostEvent | Indicates a task failed. One event should be created for each host the task fails on |
| TaskSkippedOnHostEvent | Indicates a task was skipped. One event should be created for each host the task skips on |
| HostUnreachableEvent | Indicates a host was unreachable when trying to execute a task |
| VarPromptEvent | Indicates there was an attempt to prompt for a var (which the driver won't be able to handle) |
| PlaybookResultEvent | Indicates a playbook has completed (either successfully or not) |

If you do not want these events to be logged, you may disable them with the following configuration option:

```
ansible:
  log_progress_events: True
```

> When installing on Kubernetes you may add this value to the `app.config.override` section of the Helm values file. If you have an existing installation, you can upgrade with Helm or modify the `ansible-lifecycle-driver` ConfigMap and restart the driver pods.

## Examples

**PlayStarted**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/PlayStarted
details:
  playName: Install
```

**PlayMatchedNoNoHostsEvent**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/PlayMatchedNoNoHostsEvent
details:
  playName: InstallPartA
```

**TaskStarted**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/TaskStarted
details:
  taskName: debug
  args:
    msg: An example task
  argsHidden: false
```

**TaskCompletedOnHost**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/TaskCompletedOnHost
details:
  taskName: debug
  itemLabel: null
  hostName: example-host
  delegatedHostName: null
  taskResult:
    _ansible_no_log: false
    _ansible_verbose_always: true
    msg: An example task
```

**TaskRetryOnHost**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/TaskRetryOnHost
details:
  taskName: command
  hostName: example-host
  delegatedHostName: null
  taskResult:
    _ansible_no_log: false
    _ansible_parsed: true
    _ansible_retry: true
    attempts: 1
    changed: false
    cmd: /usr/bin/false
    invocation:
      module_args:
        _raw_params: /usr/bin/false
        _uses_shell: false
        argv: null
        chdir: null
        creates: null
        executable: null
        removes: null
        stdin: null
        warn: true
    msg: '[Errno 2] No such file or directory'
    rc: 2
    retries: 3
```

**TaskFailedOnHostEvent**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/TaskFailedOnHost
details:
  taskName: command
  itemLabel: null
  hostName: example-host
  delegatedHostName: null
  taskResult:
    _ansible_no_log: false
    _ansible_parsed: true
    changed: false
    cmd: /usr/bin/false
    invocation:
      module_args:
        _raw_params: /usr/bin/false
        _uses_shell: false
        argv: null
        chdir: null
        creates: null
        executable: null
        removes: null
        stdin: null
        warn: true
    msg: '[Errno 2] No such file or directory'
    rc: 2
```

**TaskSkippedOnHostEvent**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/TaskSkippedOnHost
details:
  taskName: debug
  itemLabel: null
  hostName: example-host
  delegatedHostName: null
  taskResult:
    _ansible_no_log: false
```

**HostUnreachable**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/HostUnreachable
details:
  taskName: stat
  hostName: example-host
  delegatedHostName: null
  taskResult:
    changed: false
    msg: 'Failed to connect to the host via ssh: ssh: connect to host 9.2.0.1 port
      22: Connection timed out'
    unreachable: true
```

**PlaybookResult**
```
eventType: ResourceTransitionProgressEvent
progressEventType: ansible/PlaybookResult
details:
  plays:
  - play:
      id: 00155d76-e91e-f0fd-3b44-000000000569
      name: Install
  hostStats:
    example-host:
      changed: 0
      failures: 0
      ok: 0
      skipped: 0
      unreachable: 1
    example-host-2:
      changed: 0
      failures: 0
      ok: 1
      skipped: 0
      unreachable: 0
```