import json
import logging
import time
import os
import tempfile
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.json import CallbackModule
from ansible.plugins.loader import connection_loader
from ansible.inventory.host import Host
from jinja2 import Environment, FileSystemLoader
from ignition.model.lifecycle import LifecycleExecution, STATUS_COMPLETE, STATUS_FAILED, STATUS_IN_PROGRESS
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR, FAILURE_CODE_INTERNAL_ERROR, FAILURE_CODE_RESOURCE_NOT_FOUND
from ignition.service.config import ConfigurationPropertiesGroup
from ansibledriver.model.kubeconfig import KubeConfig

INVENTORY = "inventory"
INVENTORY_K8S = "inventory.k8s"

logger = logging.getLogger(__name__)

class AnsibleProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('ansible')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.unreachable_sleep_seconds = 5 # in seconds
        self.max_unreachable_retries = 1000
        self.output_prop_prefix = 'output__'

class AnsibleClient():
  def __init__(self, configuration):
    self.ansible_properties = configuration.property_groups.get_property_group(AnsibleProperties)

  # create a kubeconfig file based on the deployment location that can be consumed by the Python Kubernetes library
  def create_kube_config(self, deployment_location):
    return KubeConfig(deployment_location).write()

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
    options = Options(connection=connection_type,
                      listhosts=None,
                      listtasks=None,
                      listtags=None,
                      syntax=None,
                      module_path=None,
                      become=None,
                      become_method='sudo',
                      become_user='root',
                      check=False,
                      diff=False,
                      forks=20)
    passwords = {'become_pass': ''}

    # create inventory and pass to var manager
    inventory = InventoryManager(loader=loader, sources=inventory_path)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.extra_vars = all_properties
    # Setup playbook executor, but don't run until run() called
    pbex = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords
    )

    callback = ResultCallback(self.ansible_properties, request_id, lifecycle)
    pbex._tqm._stdout_callback = callback
    logger.info("Running playbook {0} with properties {1}".format(playbook_path, all_properties))
    pbex.run()
    logger.info("Playbook finished {0}".format(playbook_path))

    return callback

  def run_lifecycle_playbook(self, request):
    try:
      deployment_location = request['deployment_location']
      if not isinstance(deployment_location, dict):
        raise ValueError('Deployment Location must be an object')

      request_id = request['request_id']
      lifecycle_path = request['lifecycle_path']
      lifecycle = request['lifecycle_name']
      properties = request['properties']
      system_properties = request['system_properties']

      config_path = lifecycle_path.get_directory_tree('config')
      scripts_path = lifecycle_path.get_directory_tree('scripts')

      private_key_file_path = get_private_key_path(request)

      playbook_path = get_lifecycle_playbook_path(scripts_path, lifecycle)
      if playbook_path is not None:
        if deployment_location['type'] == 'Kubernetes':
          deployment_location['properties']['kubeconfig_path'] = self.create_kube_config(deployment_location)
          connection_type = "k8s"
          inventory_path = config_path.get_file_path(INVENTORY_K8S)
        else:
          connection_type = "ssh"
          inventory_path = config_path.get_file_path(INVENTORY)

        all_properties = {
          'properties': properties,
          'system_properties': system_properties,
          'dl_properties': deployment_location.get('properties', {})
        }

        logger.debug('config_path = ' + config_path.get_path())
        logger.debug('lifecycle_path = ' + scripts_path.get_path())
        logger.debug("playbook_path=" + playbook_path)
        logger.debug("inventory_path=" + inventory_path)

        process_templates(config_path, all_properties, private_key_file_path)

        if(os.path.exists(playbook_path)):
          # always retry on unreachable
          num_retries = self.ansible_properties.max_unreachable_retries

          for i in range(0, num_retries):
            ret = self.run_playbook(request_id, connection_type, inventory_path, playbook_path, lifecycle, all_properties)
            if not ret.host_unreachable:
              break

            time.sleep(self.ansible_properties.unreachable_sleep_seconds)

          return ret.get_result()
        else:
          msg = "No playbook to run at {0} for lifecycle {1} for request {2}".format(playbook_path, lifecycle, request_id)
          logger.info(msg)
          return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {})
      else:
        msg = "No playbook to run for lifecycle {0} for request {1} {2}".format(lifecycle, request_id, scripts_path.get_path())
        logger.error(msg)
        return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, msg), {})
    except InvalidRequestException as ire:
      return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, ire.msg), {})
    except Exception as e:
      logger.exception("Unexpected exception running playbook")
      return LifecycleExecution(request_id, STATUS_FAILED, FailureDetails(FAILURE_CODE_INTERNAL_ERROR, "Unexpected exception: {0}".format(e)), {})

class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def __init__(self, ansible_properties, request_id, lifecycle, display=None):
        super(ResultCallback, self).__init__(display)
        self.ansible_properties = ansible_properties
        self.request_id = request_id
        self.facts = {}
        self.results = []
        self.lifecycle = lifecycle

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

    def _new_play(self, play):
        return {
            'play': {
                'name': play.name,
                'id': str(play._uuid)
            },
            'tasks': []
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.name,
                'id': str(task._uuid)
            },
            'hosts': {}
        }

    def v2_playbook_on_play_start(self, play):
        logger.info('v2_playbook_on_play_start ok {0}'.format(play))
        self.results.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        logger.info('v2_playbook_on_task_start ok {0} {1}'.format(task, is_conditional))

    def v2_playbook_on_handler_task_start(self, task):
        logger.info('v2_playbook_on_handler_task_start ok {0}'.format(task))

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s

        output = {
            'plays': self.results,
            'stats': summary
        }

        logger.info('v2_playbook_on_stats {0}'.format(json.dumps(output, indent=4, sort_keys=True)))

    def v2_playbook_on_no_hosts_matched(self):
        logger.info('v2_playbook_on_no_hosts_matched')

    def v2_runner_on_unreachable(self, result, ignore_errors=False):
        """
        ansible task failed as host was unreachable
        """
        logger.info('v2_runner_on_unreachable {0}'.format(result))

        # TODO do not overwrite if already set
        self.failed_task = result._task.get_name()
        self.host_unreachable_log.append(dict(task=self.failed_task, result=result._result))
        logger.error('task: \'' + self.failed_task + '\' UNREACHABLE: ' + ' ansible playbook task ' + self.failed_task + ' host unreachable: ' + str(self.host_unreachable_log))
        self.host_unreachable = True
        self.failure_details = FailureDetails(FAILURE_CODE_RESOURCE_NOT_FOUND, 'resource unreachable')
        self.playbook_failed = True

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):
        logger.info('v2_playbook_on_vars_prompt {0}'.format(varname))

    def v2_runner_item_on_ok(self, result):
        logger.info('v2_runner_item_on_ok {0}'.format(result))

    def v2_runner_item_on_failed(self, result):
        logger.info('v2_runner_item_on_failed {0}'.format(result))

    def v2_runner_item_on_skipped(self, result):
        logger.info('v2_runner_item_on_skipped {0}'.format(result))

    def runner_on_no_hosts(self):
        logger.info('runner_on_no_hosts')

    def v2_runner_retry(self, result):
        logger.info('v2_runner_retry {0}'.format(result))

    def v2_runner_on_start(self, host, task):
        logger.info('v2_runner_on_start {0} {1}'.format(host, task))

    def runner_on_failed(self, host, res, ignore_errors=False):
        logger.info('runner_on_failed {0} {1}'.format(host, res))

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        ansible task failed
        """
        logger.info("v2_runner_on_failed {0}".format(result))

        self.host_failed = True
        self.failed_task = result._task.get_name()
        self.failure_reason = 'task ' + str(self.failed_task) + ' failed: ' + str(result._result)
        self.host_failed_log.append(dict(task=self.failed_task, result=result._result))
        self.failure_details = FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, self.failure_reason)
        self.playbook_failed = True

    def v2_runner_on_skipped(self, result):
        logger.info('v2_runner_on_skipped {0}'.format(result))

    def runner_on_ok(self, host, res):
        self._display.display('runner_on_ok {0} {1}'.format(host, res))
        logger.info('runner_on_ok {0} {1}'.format(host, res))

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        logger.info('v2_runner_on_ok {0}'.format(result))

        if 'results' in result._result.keys():
            self.facts = result._result['results']
        else:
            self.facts = result._result

        if 'ansible_facts' in self.facts:
            props = self.facts['ansible_facts']

            props = { key[8:]:value for key, value in props.items() if key.startswith(self.ansible_properties.output_prop_prefix) }

            logger.info('output props = {0}'.format(props))

            self.properties.update(props)

    def get_result(self):
      if self.playbook_failed:
        return LifecycleExecution(self.request_id, STATUS_FAILED, self.failure_details, self.properties)
      else:
        return LifecycleExecution(self.request_id, STATUS_COMPLETE, None, self.properties)

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

def process_templates(parent_dir, all_properties, private_key_file_path):
  path = parent_dir.get_path()
  logger.info('Process templates: walking {0}'.format(path))

  for root, dirs, files in os.walk(path):
    logger.debug('Process templates: files = '.format(files))
    for file in files:
        j2_env = Environment(loader=FileSystemLoader(root), trim_blocks=True)
        path = root + '/' + file
        logger.info('Process templates: writing to file {0}'.format(path))
        template = j2_env.get_template(file).render(**all_properties)
        logger.info('Process templates: template {0}'.format(template))
        with open(path, "w") as text_file:
            text_file.write(template)

def write_private_key(private_key):
  private_key_file_path = NamedTemporaryFile(delete=False)
  with open(private_key_file_path, "wb") as private_key_file:
    private_key_file.write(private_key)
  return private_key_file_path

def get_private_key_path(request):
  private_key_file_path = None

  system_properties = request['system_properties']
  private_key = system_properties.get('ansible_ssh_private_key', None)
  if private_key is None:
    properties = request['properties']
    private_key = properties.get('ansible_ssh_private_key', None)

  if private_key is not None:
    private_key_file_path = write_private_key(private_key)

  return private_key_file_path
