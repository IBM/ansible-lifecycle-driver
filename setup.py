import json
from setuptools import setup, find_namespace_packages

with open('ansibledriver/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='ansible-lifecycle-driver',
    version=_pkg_info['version'],
    author='IBM',
    description='Ansible implementation of a Lifecycle driver',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/IBM/ansible-lifecycle-driver",
    packages=find_namespace_packages(include=['ansibledriver*']),
    include_package_data=True,
    install_requires=[
        'ignition-framework=={0}'.format(_pkg_info['ignition-version']),
        'ansible==9.5.1',
        'gunicorn==21.2.0',
        'testfixtures==6.17.1',
        'openstacksdk==0.57.0',
        'boto==2.49.0',
        'boto3==1.18.42',
        'botocore==1.21.42',
        'itsdangerous==2.0.1'
    ],
    entry_points='''
        [console_scripts]
        ald-dev=ansibledriver.__main__:main
    '''
)
