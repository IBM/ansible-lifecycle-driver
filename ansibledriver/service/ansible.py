import json
import logging
import time
import os
import tempfile
from datetime import datetime
from tempfile import NamedTemporaryFile
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.json import CallbackModule
from ansible.plugins.loader import connection_loader
from ansible.inventory.host import Host
from ansible.playbook.task_include import TaskInclude
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict
from jinja2 import Environment, FileSystemLoader
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND
from ignition.service.config import ConfigurationPropertiesGroup
from ignition.service.framework import Service, Capability, interface
from ignition.utils.propvaluemap import PropValueMap
from ansibledriver.model.deploymentlocation import DeploymentLocation
from ansibledriver.model.inventory import Inventory
from ignition.model import associated_topology
from ignition.model.associated_topology import AssociatedTopology
from ansibledriver.model.progress_events import *
from ignition.service.logging import logging_context


logger = logging.getLogger(__name__)

class AnsibleProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('ansible')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.unreachable_sleep_seconds = 5 # in seconds
        self.max_unreachable_retries = 1000
        self.output_prop_prefix = 'output__'
        self.tmp_dir = '.'
        self.log_progress_events = True


class AnsibleClientCapability(Capability):

    @interface
    def run_lifecycle_playbook(self, request):
      pass


class AnsibleClient(Service, AnsibleClientCapability):
  def __init__(self, configuration, **kwargs):
    self.ansible_properties = configuration.property_groups.get_property_group(AnsibleProperties)
    if 'render_context_service' not in kwargs:
      raise ValueError('render_context_service argument not provided')
    self.render_context_service = kwargs.get('render_context_service')
    if 'templating' not in kwargs:
      raise ValueError('templating argument not provided')
    self.templating = kwargs.get('templating')
    if 'event_logger' not in kwargs:
      raise ValueError('event_logger argument not provided')
    self.event_logger = kwargs.get('event_logger')

  def run_playbook(self, request_id, connection_type, inventory_path, playbook_path, lifecycle, all_properties):
    Options = namedtuple('Options', ['connection',
                                     'forks',
                                     'become',
                                     'become_method',
                                     'become_user',
                                     'listhosts',
                                     'listtasks',
                                     'listtags',
                                     'syntax',
                                     'module_path',
                                     'check',
                                     'diff'])
    # initialize needed objects
    loader = DataLoader()
    
    context.CLIARGS = ImmutableDict(connection=connection_type, 
                                    module_path=None, 
                                    forks=20, 
                                    become=None,
                                    become_method='sudo', 
                                    become_user='root', 
                                    check=False, 
                                    diff=False,
                                    listhosts=None, 
                                    listtasks=None, 
                                    listtags=None, 
                                    syntax=None,
                                    start_at_task=None, 
                                    verbosity=1)

    passwords = {'become_pass': ''}

    # create inventory and pass to var manager
    inventory = InventoryManager(loader=loader, sources=inventory_path)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager._extra_vars = all_properties
    # Setup playbook executor, but don't run until run() called
    pbex = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords=passwords
    )

    callback = ResultCallback(self.ansible_properties, request_id, lifecycle, self.event_logger)
    pbex._tqm._stdout_callback = callback

    pbex.run()
    logger.debug(f'Playbook finished {playbook_path}')

    return callback

  def run_lifecycle_playbook(self, request):
    driver_files = request['driver_files']
    key_property_processor = None
    location = None

    try:
      request_id = request['request_id']
      lifecycle = request['lifecycle_name']
      resource_properties = request.get('resource_properties', {})
      system_properties = request.get('system_properties', {})
      request_properties = request.get('request_properties', {})
      associated_topology = request.get('associated_topology', None)
      
      location = DeploymentLocation.from_request(request)

      config_path = driver_files.get_directory_tree('config')
      scripts_path = driver_files.get_directory_tree('scripts')

      key_property_processor = KeyPropertyProcessor(resource_properties, system_properties, location.properties())

      playbook_path = get_lifecycle_playbook_path(scripts_path, lifecycle)
      if playbook_path is not None:
        if not os.path.exists(playbook_path):
          return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Playbook path does not exist"), {})

        inventory = Inventory(driver_files, location.infrastructure_type)

        # process key properties by writing them out to a temporary file and adding an
        # entry to the property dictionary that maps the "[key_name].path" to the key file path
        key_property_processor.process_key_properties()

        logger.debug(f'Handling request {request_id} with config_path: {config_path.get_path()} driver files path: {scripts_path.get_path()} resource properties: {resource_properties} system properties {system_properties} request properties {request_properties}')

        all_properties = self.render_context_service.build(system_properties, resource_properties, request_properties, location.deployment_location(), associated_topology)

        process_templates(config_path, self.templating, all_properties)

        # always retry on unreachable
        num_retries = self.ansible_properties.max_unreachable_retries

        for i in range(0, num_retries):
          if i>0:
            logger.debug('Playbook {0}, unreachable retry attempt {1}/{2}'.format(playbook_path, i+1, num_retries))
          start_time = datetime.now()
          ret = self.run_playbook(request_id, location.connection_type, inventory.get_inventory_path(), playbook_path, lifecycle, all_properties)
          if not ret.host_unreachable:
            break
          end_time = datetime.now()
          if self.ansible_properties.unreachable_sleep_seconds > 0:
            # Factor in that the playbook may have taken some time to determine is was unreachable
            # by using the unreachable_sleep_seconds value as a minimum amount of time for the delay 
            delta = end_time - start_time
            retry_seconds = max(0, self.ansible_properties.unreachable_sleep_seconds-int(delta.total_seconds()))
            time.sleep(retry_seconds)

        return ret.get_result()
      else:
        msg = "No playbook to run at {0} for lifecycle {1} for request {2}".format(playbook_path, lifecycle, request_id)
        logger.debug(msg)
        return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {})
    except InvalidRequestException as ire:
      return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, ire.msg), {})
    except Exception as e:
      logger.exception("Unexpected exception running playbook")
      return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {})
    finally:
      if location is not None:
        location.cleanup()

      if key_property_processor is not None:
        key_property_processor.clear_key_files()

      keep_files = request.get('keep_files', False)
      if not keep_files and driver_files is not None:
        try:
          logger.debug('Attempting to remove lifecycle scripts at {0}'.format(driver_files.root_path))
          driver_files.remove_all()
        except Exception as e:
          logger.exception('Encountered an error whilst trying to clear out lifecycle scripts directory {0}: {1}'.format(driver_files.root_path, str(e)))


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def __init__(self, ansible_properties, request_id, lifecycle, event_logger, display=None):
        super(ResultCallback, self).__init__(display)
        self.ansible_properties = ansible_properties
        self.request_id = request_id
        self.facts = {}
        self.plays = []
        self.lifecycle = lifecycle
        self.event_logger = event_logger

        self.playbook_failed = False

        self.host_unreachable = False
        self.host_failed = False
        self.host_unreachable_log = []
        self.host_failed_log = []

        self.resource_id = None
        self.properties = {}
        self.internal_properties = {}
        self.internal_resource_instances = []
        self.failure_code = ''
        self.failure_reason = ''
        
        self.associated_topology = None

    def _new_play(self, play):
        return {
            'play': {
                'name': play.get_name().strip(),
                'id': str(play._uuid)
            }
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.get_name().strip(),
                'id': str(task._uuid)
            },
            'hosts': {}
        }

    def v2_playbook_on_play_start(self, play):
        """
        Called when a play begins
        Note: ONE playbook can have MANY plays
        """
        logger.debug('v2_playbook_on_play_start: {0}'.format(play))
        if self.ansible_properties.log_progress_events:
            play_name = play.get_name().strip()
            event = PlayStartedEvent(play_name=play_name)
            self.event_logger.add(event)
        self.plays.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        """
        Called when a task starts 
        Note: even if a task is going to run on multiple hosts, this function is only called ONCE
        """
        logger.debug('v2_playbook_on_task_start: {0} (is_conditional={1})'.format(task, is_conditional))
        self._log_task_start(task)

    def v2_playbook_on_handler_task_start(self, task):
        logger.debug('v2_playbook_on_handler_task_start: {0}'.format(task))
        self._log_task_start(task, prefix='Handler/')

    def _log_task_start(self, task, prefix=None):
        if self.ansible_properties.log_progress_events:
            if prefix is None:
              prefix = ''
            task_name = '{0}{1}'.format(prefix, task.get_name().strip())
            event = TaskStartedEvent(task_name=task_name)
            if not task.no_log:
              # Include args if the task has not been configured with the no_log option
              for arg_name, arg_value in task.args.items():
                event.args[str(arg_name)] = str(arg_value)
            else:
              event.args_hidden = True
            self.event_logger.add(event)

    def v2_playbook_on_stats(self, stats):
        """
        Called at the end of playbook execution (even in failure)
        """
        logger.debug('v2_playbook_on_stats: {0}'.format(stats))
        if self.ansible_properties.log_progress_events:
            hosts = sorted(stats.processed.keys())
            host_stats = {}
            for h in hosts:
                host_stats[h] = stats.summarize(h)
            
            event = PlaybookResultEvent(plays=self.plays, host_stats=host_stats)
            self.event_logger.add(event)

    def v2_playbook_on_no_hosts_matched(self):
        """
        Called if a play did not match any hosts (will be called after v2_playbook_on_play_start if this occurs)
        """
        logger.debug('v2_playbook_on_no_hosts_matched')
        if self.ansible_properties.log_progress_events:
            # We can assume it's the last play that started. Need to be wary of the "free" strategy but I think this works even then
            if len(self.plays) == 0:
                play_name = 'Unknown'
            else:
                play_name = self.plays[-1]['play']['name']
            event = PlayMatchedNoNoHostsEvent(play_name=play_name)
            self.event_logger.add(event)

    def v2_runner_on_unreachable(self, result, ignore_errors=False):
        """
        Called if a host is unreachable on execution of a task
        """
        logger.debug('v2_runner_on_unreachable: {0}'.format(result._task))
        self.__handle_unreachable(result)
        logger.error('task: \'' + self.failed_task + '\' UNREACHABLE: ' + ' ansible playbook task ' + self.failed_task + ' host unreachable: ' + str(self.host_unreachable_log))

    def _log_unreachable_event(self, result):
        if self.ansible_properties.log_progress_events:
            task_name = result._task.get_name()
            self._clean_results(result._result, result._task.action)
            task_result = result._result
            event = HostUnreachableEvent(task_name=task_name, host_name=result._host.get_name().strip(), task_result=task_result)
            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars is not None:
                event.delegated_host_name = delegated_vars['ansible_host']
            self.event_logger.add(event)

    def __handle_unreachable(self, result):
        self.failed_task = result._task.get_name()
        self.host_unreachable_log.append(dict(task=self.failed_task, result=result._result))
        self.host_unreachable = True
        self.failure_reason = 'Resource unreachable (task ' + str(self.failed_task) + ' failed: ' + str(result._result) + ')'
        self.failure_details = FailureDetails(FAILURE_CODE_RESOURCE_NOT_FOUND, self.failure_reason)
        self.playbook_failed = True
        self._log_unreachable_event(result)

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
        """
        Called when a var_prompt is used in a playbook, which we can't support because the playbook is not running in an interactive shell
        """
        logger.debug('v2_playbook_on_vars_prompt: {0}'.format(varname))
        if self.ansible_properties.log_progress_events:
            event = VarPromptEvent(var_name=varname)
            self.event_logger.add(event)

    def runner_on_no_hosts(self):
        logger.debug('runner_on_no_hosts')

    def v2_runner_retry(self, result):
        """
        Called when a task is retried
        """
        logger.debug('v2_runner_retry: {0}'.format(result))
        if self.ansible_properties.log_progress_events:
            host_name = result._host.get_name().strip()
            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars is not None:
                delegated_host_name = delegated_vars['ansible_host']
            else:
                delegated_host_name = None
            self._clean_results(result._result, result._task.action)
            task_name = result._task.get_name().strip()
            event = TaskRetryOnHostEvent(task_name, host_name, result._result, delegated_host_name=delegated_host_name)
            self.event_logger.add(event)

    def v2_runner_on_start(self, host, task):
        """
        Called when a task starts on a particular host (Ansible v2.8+)
        """
        logger.debug('v2_runner_on_start: host={0}, task={1}'.format(host, task))
        if self.ansible_properties.log_progress_events:
            task_name = task.get_name().strip()
            host_name = host.get_name().strip()
            event = TaskStartedOnHostEvent(task_name=task_name, host_name=host_name)
            if not task.no_log:
              # Include args if the task has not been configured with the no_log option
              for arg_name, arg_value in task.args.items():
                event.args[str(arg_name)] = str(arg_value)
            else:
              event.args_hidden = True
            self.event_logger.add(event)

    def runner_on_failed(self, host, res, ignore_errors=False):
        logger.debug('runner_on_failed: host={0}, result={1}'.format(host, res))
    
    def _log_event_for_failed_task(self, result, is_item=False):
        if self.ansible_properties.log_progress_events:
            host_name = result._host.get_name().strip()
            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars is not None:
                delegated_host_name = delegated_vars['ansible_host']
            else:
                delegated_host_name = None
            if is_item:
                item_label = self._get_item_label(result._result)
            else:
                item_label = None
            self._clean_results(result._result, result._task.action)
            task_name = result._task.get_name().strip()
            event = TaskFailedOnHostEvent(task_name, host_name, result._result, item_label=item_label, delegated_host_name=delegated_host_name)
            self.event_logger.add(event)

    def v2_runner_item_on_failed(self, result):
        """
        Called when task execution fails for an item in a loop (e.g. with_items)
        """
        logger.debug('v2_runner_item_on_failed: {0}'.format(result))
        self._log_event_for_failed_task(result, is_item=True)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        Called when a task fails
        Note: even when a loop is used (so v2_runner_item_on_failed/v2_runner_item_on_ok is called for each item) this function is called at the end, when all items have been attempted but one has failed
        """
        logger.debug("v2_runner_on_failed: task={0}, result={1}, task_fields={2}".format(result._task, result._result, result._task_fields))
        # TODO: handle ignore_errors?
        self.failed_task = result._task.get_name()
        if 'msg' in result._result and 'Timeout' in result._result['msg'] and 'waiting for privilege escalation prompt' in result._result['msg']:
            logger.info('Failure to be treated as unreachable:  task ' + str(self.failed_task) + ' failed: ' + str(result._result))
            self.__handle_unreachable(result)
        elif 'module_stderr' in result._result and result._result['module_stderr'].startswith('ssh:') and 'Host is unreachable' in result._result['module_stderr']:
            logger.info('Failure to be treated as unreachable: task ' + str(self.failed_task) + ' failed: ' + str(result._result))
            self.__handle_unreachable(result)
        else:
          self.host_failed = True
          self.failure_reason = 'task ' + str(self.failed_task) + ' failed: ' + str(result._result)
          self.host_failed_log.append(dict(task=self.failed_task, result=result._result))
          self.failure_details = FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, self.failure_reason)
          self.playbook_failed = True
          self._log_event_for_failed_task(result)

    def _log_event_for_skipped_task(self, result, is_item=False):
        if self.ansible_properties.log_progress_events:
            host_name = result._host.get_name().strip()
            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars is not None:
                delegated_host_name = delegated_vars['ansible_host']
            else:
                delegated_host_name = None
            if is_item:
                item_label = self._get_item_label(result._result)
            else:
                item_label = None
            self._clean_results(result._result, result._task.action)
            task_name = result._task.get_name().strip()
            event = TaskSkippedOnHostEvent(task_name, host_name, result._result, item_label=item_label, delegated_host_name=delegated_host_name)
            self.event_logger.add(event)
        
    def v2_runner_item_on_skipped(self, result):
        """
        Called when task execution is skipped an item in a loop (e.g. with_items)
        """
        logger.debug('v2_runner_item_on_skipped: {0}'.format(result))
        self._log_event_for_skipped_task(result, is_item=True)

    def v2_runner_on_skipped(self, result):
        """
        Called when task execution is skipped
        """
        logger.debug('v2_runner_on_skipped: {0}'.format(result))
        self._log_event_for_skipped_task(result, is_item=True)

    def runner_on_ok(self, host, res):
        logger.debug('runner_on_ok: host={0} res={1}'.format(host, res))

    def _log_event_for_ok_task(self, result, is_item=False):
        if self.ansible_properties.log_progress_events:
            host_name = result._host.get_name().strip()
            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars is not None:
                delegated_host_name = delegated_vars['ansible_host']
            else:
                delegated_host_name = None
            if is_item:
                item_label = self._get_item_label(result._result)
            else:
                item_label = None
            self._clean_results(result._result, result._task.action)
            task_name = result._task.get_name().strip()
            event = TaskCompletedOnHostEvent(task_name, host_name, result._result, item_label=item_label, delegated_host_name=delegated_host_name)
            self.event_logger.add(event)
            self._generate_additional_logs(result)

    def v2_runner_item_on_ok(self, result):
        """
        Called when task execution completes for an item in a loop (e.g. with_items)
        """
        logger.debug('v2_runner_item_on_ok: {0}'.format(result))
        if isinstance(result._task, TaskInclude):
            logger.debug('Skipping v2_runner_item_on_ok call for TaskInclude')
            return
        self._log_event_for_ok_task(result, is_item=True)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        Called when task execution completes (called for each host the task executes against)
        Note: even when a loop is used (so v2_runner_item_on_ok is called for each successful item) this function is called at the end, when all items have succeeded
        """
        logger.debug('v2_runner_on_ok: {0}'.format(result))

        props = []
        if 'results' in result._result.keys():
            self.facts = result._result['results']
            props = [ item['ansible_facts'] for item in self.facts if 'ansible_facts' in item ]
        else:
            self.facts = result._result
            if 'ansible_facts' in self.facts:
                props = [ self.facts['ansible_facts'] ]
            
        for prop in props:
            for key, value in prop.items():
                if key.startswith(self.ansible_properties.output_prop_prefix):
                    output_facts = { key[len(self.ansible_properties.output_prop_prefix):]: value }
                    logger.debug('output props = {0}'.format(output_facts))
                    self.properties.update(output_facts)
                elif key == 'associated_topology':
                    try:
                        logger.info('associated_topology = {0}'.format(associated_topology)) 
                        self.associated_topology = AssociatedTopology.from_dict(value)
                    except ValueError as ve:
                      self.failure_reason = f'An error has occurred while parsing the ansible fact \'{key}\'. {ve}'
                      self.failure_details = FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, self.failure_reason)
                      self.playbook_failed = True
                    except Exception as e:
                      self.failure_reason = f'An internal error has occurred. {e}'
                      self.failure_details = FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, self.failure_reason)
                      self.playbook_failed = True
        self._log_event_for_ok_task(result)
                
    def get_result(self):
      if self.playbook_failed:
        return LifecycleExecution(self.request_id, STATUS_FAILED, self.failure_details, self.properties)
      else:
        return LifecycleExecution(self.request_id, STATUS_COMPLETE, None, self.properties, self.associated_topology)

    def _generate_additional_logs(self, result):
      # Added logic to print logs for custom ansible module : ibm_cp4na_log_message
      try:
          if('message_direction' in result._result and 'external_request_id' in result._result and 'message_type' in result._result and 'protocol' in result._result):
              message_direction = result._result['message_direction']
              external_request_id = result._result['external_request_id']
              content_type = result._result['content_type']
              message_data = result._result['message_data']
              message_type = result._result['message_type']
              protocol = result._result['protocol']
              protocol_metadata = result._result['protocol_metadata']

              logging_context_dict = {'messageDirection' : message_direction, 'tracectx.externalRequestId' : external_request_id, 'ContentType' : content_type,
                                      'messageType' : message_type, 'protocol' : protocol.lower(), 'protocol_metadata' : protocol_metadata, 'tracectx.driverrequestid' : self.request_id}
              logging_context.set_from_dict(logging_context_dict)

              logger.info(message_data)
      finally:
          if('messageDirection' in logging_context.data):
              logging_context.data.pop("messageDirection")
          if('tracectx.externalRequestId' in logging_context.data):
              logging_context.data.pop("tracectx.externalRequestId")
          if('ContentType' in logging_context.data):
              logging_context.data.pop("ContentType")
          if('messageType' in logging_context.data):
              logging_context.data.pop("messageType")
          if('protocol' in logging_context.data):
              logging_context.data.pop("protocol")
          if('protocol_metadata' in logging_context.data):
              logging_context.data.pop("protocol_metadata")
          if('tracectx.driverrequestid' in logging_context.data):
              logging_context.data.pop("tracectx.driverrequestid")

class InvalidRequestException(Exception):
  """Raised when a REST request is invalid
     Attributes:
       msg - failure message
  """

  def __init__(self, msg):
    self.msg = msg

def get_lifecycle_playbook_path(root_path, transition_name):
    try:
      return root_path.get_file_path(transition_name + ".yaml")
    except ValueError as e:
      # no playbook
      try:
        return root_path.get_file_path(transition_name + ".yml")
      except ValueError as e:
        # no playbook
        return None

def process_templates(parent_dir, templating, all_properties):
  path = parent_dir.get_path()
  logger.debug('Process templates: walking {0}'.format(path))

  for root, dirs, files in os.walk(path):
    logger.debug('Process templates: files = '.format(files))
    for file in files:
        j2_env = Environment(loader=FileSystemLoader(root), trim_blocks=True)
        path = root + '/' + file
        logger.debug(f'Processing template {file}')

        with open(path, "r") as template_file:
          try:
            template_content = template_file.read()
            content = templating.render(template_content, all_properties)
            logger.debug('Wrote process template to file {0}'.format(path))
            with open(path, "w") as template_file_write:
                template_file_write.write(content)
          except UnicodeDecodeError as ude:
            # skip this file, not a text file
            pass




class KeyPropertyProcessor():
  def __init__(self, properties, system_properties, dl_properties):
    self.properties = properties
    self.system_properties = system_properties
    self.dl_properties = dl_properties
    self.key_files = []

  """
  Process (input) key properties by writing the private key out to a file so that it can be
  referenced in e.g. inventory files.
  """
  def process_key_properties(self):
    self.process_keys(self.properties)
    self.process_keys(self.system_properties)
    self.process_keys(self.dl_properties)

  def process_keys(self, properties):
    for prop in properties.get_keys().items_with_types():
      self.write_private_key(properties, prop[0], prop[1])

  def write_private_key(self, properties, key_prop_name, private_key):
    with NamedTemporaryFile(delete=False, mode='w') as private_key_file:
      logger.debug('Writing private key file {0}'.format(private_key_file.name))
      private_key_value = private_key.get('privateKey', None)
      private_key_file.write(private_key_value)
      private_key_file.flush()
      self.key_files.append(private_key_file)

      logger.debug('Setting property {0}_path'.format(key_prop_name))
      properties[key_prop_name + '_path'] = private_key_file.name

      logger.debug('Setting property {0}_name'.format(key_prop_name))
      key_name = private_key.get('keyName', None)
      properties[key_prop_name + '_name'] = key_name

  """
  Remove any private key files generated during the Ansible run.
  """
  def clear_key_files(self):
    for key_file in self.key_files:
      logger.debug('Removing private key file {0}'.format(key_file.name))
      os.unlink(key_file.name)
