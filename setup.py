import json
from setuptools import setup, find_namespace_packages

with open('ansibledriver/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='ansible-lifecycle-driver',
    version=_pkg_info['version'],
    author='Accanto Systems',
    description='Ansible implementation of a Lifecycle driver',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/accanto-systems/ansible-lifecycle-driver",
    packages=find_namespace_packages(include=['ansibledriver*']),
    include_package_data=True,
    install_requires=[
        'ignition-framework{0}'.format(_pkg_info['ignition-version']),
        'ansible==2.7.16',
        'Jinja2>=2.10.1,<3.0',
        'uwsgi>=2.0.18,<3.0',
        'gunicorn>=19.9.0,<20.0',
        'testfixtures>=6.12.1,<7.0',
        'openshift>=0.6',
        'PyYAML>=3.11'
    ],
    entry_points='''
        [console_scripts]
        ald-dev=ansibledriver.__main__:main
    ''',
    scripts=['ansibledriver/bin/ald-uwsgi', 'ansibledriver/bin/ald-gunicorn', 'ansibledriver/bin/ald']
)