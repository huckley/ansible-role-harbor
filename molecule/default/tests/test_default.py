
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """

    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution

    if distribution in ['debian', 'ubuntu']:
        os = "debian"
    elif distribution in ['centos', 'redhat', 'ol']:
        os = "redhat"
    elif distribution in ['arch']:
        os = "archlinux"

    print(" -> {} / {}".format(distribution, os))

    file_defaults = "file={}/defaults/main.yaml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yaml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yaml name=test_vars".format(molecule_dir)
    file_distibution = "file={}/vars/{}.yaml name=role_distibution".format(base_dir, os)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_directory(host, get_vars):

    # pp.pprint(get_vars)

    dir = host.file(get_vars.get('harbor_datadir'))
    assert dir.is_directory


@pytest.mark.parametrize("files", [
    "harbor/prepare",
])
def test_files(host, get_vars, files):
    dir = host.file(get_vars.get('harbor_install_dir'))
    f = host.file("{0}/{1}".format(dir.linked_to, files))
    assert f.is_file
