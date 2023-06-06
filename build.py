import os
import subprocess
import sys
import shutil
import json
import argparse
import jinja2 as jinja
import platform
import git

PKG_ROOT = 'ansibledriver'
PKG_INFO = 'pkg_info.json'
DIST_DIR = 'dist'
WHL_FORMAT = 'ansible_lifecycle_driver-{version}-py3-none-any.whl'

DOCS_FORMAT = 'ansible-lifecycle-driver-{version}-docs'
DOCS_DIR = 'docs'

DOCKER_WHLS_DIR = 'whls'
DOCKER_PATH = 'docker'
DOCKER_IMG_NAME = 'ansible-lifecycle-driver'
DOCKER_REGISTRY = 'icr.io/cp4na-drivers'

HELM_CHART_PATH = os.path.join('helm', 'ansiblelifecycledriver')
HELM_CHART_NAME = 'ansiblelifecycledriver'
HELM_CHART_NAME_FORMAT = 'ansiblelifecycledriver-{0}.tgz'

parser=argparse.ArgumentParser()

parser.add_argument('--release', help='Include this flag to publish this build as an official release', default=False, action='store_true')
parser.add_argument('--version', help='version to set for the release')
parser.add_argument('--post-version', help='version to set after the release')
parser.add_argument('--ignition-version', help='Set the ignition version for the release')
parser.add_argument('--skip-tests', default=False, action='store_true')
parser.add_argument('--skip-docker', default=False, action='store_true')
parser.add_argument('--skip-helm', default=False, action='store_true')
parser.add_argument('--ignition-whl', help='Add a custom Ignition whl to the build by path (useful when working with a dev version of Ignition)')

args = parser.parse_args()

class BuildError(Exception):
    pass

class Secret:

    def __init__(self, value):
        self.value = value

class Stage:

    def __init__(self, builder, title):
        self.builder = builder
        self.title = title
        self.exit_reason = None
        self.exit_code = 0

    def __enter__(self):
        print('================================================')
        print('{0}'.format(self.title))
        print('================================================')
        return self

    def __exit__(self, type, err_value, traceback):
        if err_value != None:
            # Legit python error thrown
            print('ERROR: {0}\n'.format(str(err_value)))
            try:
                self.builder.report()
            except e:
                pass
            return    
        if self.exit_code != 0:
            if self.exit_reason != None:
                print(self.exit_reason)
            self.builder.report()
            exit(self.exit_code)
        else:
            print('')

    def _cmd_exit(self, exit_code):
        self.exit_code = exit_code

    def exit_with_error(self, exit_code, reason):
        self.exit_reason = reason
        self.exit_code = exit_code

    def run_cmd(self, *cmd):
        print('Executing: {0}'.format(' '.join(cmd)))
        working_dir = self.builder.project_path if self.builder.project_path != None and self.builder.project_path != '' else None
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=working_dir)
        process.communicate()
        if process.returncode != 0:
            return  self._cmd_exit(process.returncode)

class Builder:

    def __init__(self):
        self.project_path = os.path.dirname(__file__)
        self.project_path_is_current_dir = False
        if self.project_path == None or self.project_path == '':
            self.project_path_is_current_dir = True
        self.stages = []
        self.project_version = None
        self.py_normalized_version = None

    def report(self):
        print('================================================')
        print('Build Result')
        print('================================================')
        for s in self.stages:
            if s.exit_code == 0:
                print('  {0} - OK'.format(s.title))
            else:
                print('  {0} - FAILED'.format(s.title))
        print(' ')

    def stage(self, title):
        stage = Stage(self, title)
        self.stages.append(stage)
        return stage

    def _announce_build_location(self):
        if self.project_path_is_current_dir:
            print('Building at: ./')
        else:
            print('Building at: {0}'.format(self.project_path))

    def doIt(self):
        self._announce_build_location()
        self.validate()
        self.prepare()
        if args.release == True:
            self.release()
        else:
            self.build()
        self.tidy_up()
        self.report()

    def validate(self):
        if args.release:
            if args.version is None:
                raise ValueError('Must set --version when releasing')
            if args.post_version is None:
                raise ValueError('Must set --post-version when releasing')

    def prepare(self):
        if args.version is not None:
            self.set_version()
        self.determine_version()
    
    def tidy_up(self):
        if args.post_version is not None:
            self.set_post_version()
            if args.release:
                self.push_post_release_git_changes()
  
    def build(self):
        self.init_artifacts_directory()
        self.run_unit_tests()
        self.build_python_wheel()
        self.pkg_docs()
        if args.skip_docker is not True:
            self.build_docker_image()
        if args.skip_helm is not True:
            self.build_helm_chart()

    def release(self):
        self.build()
        if args.skip_docker is not True:
            self.push_docker_image()
        self.push_release_git_changes()

    def init_artifacts_directory(self):
        self.artifacts_path = os.path.join(self.project_path, 'release-artifacts')
        if os.path.exists(self.artifacts_path):
            shutil.rmtree(self.artifacts_path)
        os.makedirs(self.artifacts_path)

    def set_version(self):
        with self.stage('Updating Version') as s:
            pkg_info_path = os.path.join(self.project_path, PKG_ROOT, PKG_INFO)
            print('Updating version in {0} to {1}'.format(pkg_info_path, args.version))
            with open(pkg_info_path, 'r') as f:
                pkg_info_data = json.load(f)
            pkg_info_data['version'] = args.version
            if args.ignition_version:
                print('Updating Ignition version in {0} to {1}'.format(pkg_info_path, args.ignition_version))
                pkg_info_data['ignition-version'] = args.ignition_version
            with open(pkg_info_path, 'w') as f:
                json.dump(pkg_info_data, f) 
    
    def set_post_version(self):
        with self.stage('Updating Post Build Version') as s:
            pkg_info_path = os.path.join(self.project_path, PKG_ROOT, PKG_INFO)
            print('Updating version in {0} to {1}'.format(pkg_info_path, args.post_version))
            with open(pkg_info_path, 'r') as f:
                pkg_info_data = json.load(f)
            pkg_info_data['version'] = args.post_version
            with open(pkg_info_path, 'w') as f:
                json.dump(pkg_info_data, f)

    def determine_version(self):
        with self.stage('Gathering Version') as s:
            pkg_info_path = os.path.join(self.project_path, PKG_ROOT, PKG_INFO)
            print('Reading version from {0}'.format(pkg_info_path))
            with open(pkg_info_path, 'r') as f:
                pkg_info_data = json.load(f)
            if 'version' not in pkg_info_data:
                return s.exit_with_error(1, '\'version\' not found in {0}'.format(pkg_info_path))
            else:
                self.project_version = pkg_info_data['version']
                print('Found version is: {0}'.format(self.project_version))
                self.py_normalized_version = pkg_info_data['version']
                self.py_normalized_version = self.py_normalized_version.replace('-alpha-', 'a')
                self.py_normalized_version = self.py_normalized_version.replace('-beta-', 'b')
                self.py_normalized_version = self.py_normalized_version.replace('-rc', 'rc')

    def run_unit_tests(self):
        with self.stage('Run Unit Tests') as s:
            s.run_cmd('python3', '-m', 'unittest')

    def build_python_wheel(self):
        with self.stage('Build Wheel') as s:
            print('Cleaning directory: {0}'.format(DIST_DIR))
            dist_path = os.path.join(self.project_path, DIST_DIR)
            if os.path.exists(dist_path):
                shutil.rmtree(dist_path)
            s.run_cmd('python3', 'setup.py', 'bdist_wheel')

    def build_docker_image(self):
        self._build_docker_image('Build Docker Image', os.path.join(self.project_path, DOCKER_PATH), DOCKER_IMG_NAME)

    def _build_docker_image(self, title, docker_context_path, docker_img_name):
        with self.stage(title) as s:
            docker_whls_path = os.path.join(docker_context_path, DOCKER_WHLS_DIR)
            print('Cleaning directory: {0}'.format(docker_whls_path))
            if os.path.exists(docker_whls_path):
                shutil.rmtree(docker_whls_path)
            os.mkdir(docker_whls_path)
            src_whl_path = os.path.join(self.project_path, DIST_DIR, WHL_FORMAT.format(version=self.py_normalized_version))
            if not os.path.exists(src_whl_path):
                return s.exit_with_error(1, 'Could not find whl at: {0}'.format(src_whl_path))
            else:
                dest_whl = os.path.join(docker_whls_path, WHL_FORMAT.format(version=self.py_normalized_version))
                shutil.copyfile(src_whl_path, dest_whl)
            if args.ignition_whl is not None:
                if not os.path.exists(args.ignition_whl):
                    return s.exit_with_error(1, 'Could not find Ignition whl at: {0}'.format(args.ignition_whl))
                dest_ign_whl = os.path.join(docker_whls_path, os.path.basename(args.ignition_whl))
                print('Copying Ignition whl at {0} to {1}'.format(args.ignition_whl, dest_ign_whl))
                shutil.copyfile(args.ignition_whl, dest_ign_whl)
            img_tag = '{0}:{1}'.format(docker_img_name, self.project_version)
            s.run_cmd('docker', 'build', '--pull', '-t', img_tag, '{0}'.format(docker_context_path))

    def build_helm_chart(self):
        with self.stage('Build Helm Chart') as s:
            tmp_helm_path = os.path.join(self.project_path, 'helm', 'build', HELM_CHART_NAME)
            if os.path.exists(tmp_helm_path):
                shutil.rmtree(tmp_helm_path)
            os.makedirs(tmp_helm_path)
            helm_chart_path = os.path.join(self.project_path, HELM_CHART_PATH)
            template_loader = jinja.FileSystemLoader(searchpath=helm_chart_path)
            template_env = jinja.Environment(variable_start_string='${', variable_end_string='}', loader=template_loader)
            resolvable_props = {'version': self.project_version}
            for item in os.listdir(helm_chart_path):
                full_item_path = os.path.join(helm_chart_path, item)
                if os.path.isdir(full_item_path):
                    self._template_helm_chart_directory(helm_chart_path, template_env, full_item_path, tmp_helm_path, resolvable_props)
                else:
                    self._template_helm_chart_file(helm_chart_path, template_env, full_item_path, tmp_helm_path, resolvable_props)
            pkg_path = os.path.join(self.project_path, 'pkg')
            s.run_cmd('helm', 'package', '--destination', self.artifacts_path, '{0}'.format(tmp_helm_path))
            shutil.rmtree(os.path.join(self.project_path, 'helm', 'build'))
    
    def _template_helm_chart_directory(self, base_path, template_env, orig_dir_path, target_parent_path, resolvable_props):
        orig_dir_name = os.path.basename(orig_dir_path)
        new_dir_path = os.path.join(target_parent_path, orig_dir_name)
        if os.path.exists(new_dir_path):
            shutil.rmtree(new_dir_path)
        else:
            os.mkdir(new_dir_path)
        for item in os.listdir(orig_dir_path):
            full_item_path = os.path.join(orig_dir_path, item)
            if os.path.isdir(full_item_path):
                self._template_helm_chart_directory(base_path, template_env, full_item_path, new_dir_path, resolvable_props)
            else:
                self._template_helm_chart_file(base_path, template_env, full_item_path, new_dir_path, resolvable_props)

    def _template_helm_chart_file(self, base_path, template_env, orig_file_path, target_parent_path, resolvable_props):
        file_rel_path = os.path.relpath(orig_file_path, base_path)
        template = template_env.get_template(file_rel_path)
        output = template.render(resolvable_props)
        orig_file_name = os.path.basename(orig_file_path)
        new_file_path = os.path.join(target_parent_path, orig_file_name)
        with open(new_file_path, 'w') as f:
            f.write(output)

    def push_docker_image(self):
        self._push_docker_image('Push Docker Image', '{0}:{1}'.format(DOCKER_IMG_NAME, self.project_version))

    def _push_docker_image(self, title, current_docker_img_tag):
        with self.stage(title) as s:
            new_tag = DOCKER_REGISTRY + '/' + current_docker_img_tag
            s.run_cmd('docker', 'tag', current_docker_img_tag, new_tag)
            s.run_cmd('docker', 'push', new_tag)

    def pkg_docs(self):
        with self.stage('Package Docs') as s:
            print('Packaging docs at {0}'.format(DOCS_DIR))
            docs_output = DOCS_FORMAT.format(version=self.project_version)
            docs_output_file = os.path.join(self.artifacts_path, docs_output + '.tgz')
            transform_command = 's/{0}/{1}/'.format(DOCS_DIR, docs_output)
            # Note that a system running on Mac will return 'Darwin' for platform.system()
            if platform.system() == 'Darwin':
                transform_command = '/{0}/{1}/'.format(DOCS_DIR, docs_output)                
                s.run_cmd('tar', '-cvz', '-s', transform_command, '-f', docs_output_file, DOCS_DIR+'/')
            else:
                s.run_cmd('tar', '-cvzf', docs_output_file, DOCS_DIR+'/', '--transform', transform_command)

    def push_release_git_changes(self):
        with self.stage('Commit Release Changes') as s:
            repo = git.Repo(self.project_path)
            repo.index.add([os.path.join(PKG_ROOT, PKG_INFO)])
            repo.index.commit('Update version for release')
            if args.version in repo.tags:
                repo.delete_tag(args.version)
            repo.create_tag(args.version)

    def push_post_release_git_changes(self):
        with self.stage('Commit Post Release Changes') as s:
            repo = git.Repo(self.project_path)
            repo.index.add([os.path.join(PKG_ROOT, PKG_INFO)])
            repo.index.commit('Update version for development')
            origin = repo.remote('origin')
            origin.push(tags=True)
            origin.push()

def main():
  builder = Builder()
  builder.doIt()

if __name__== "__main__":
  main()

