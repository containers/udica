# Copyright (C) 2019 Jan Zarsky, <jzarsky@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import unittest
from os.path import exists
from shutil import rmtree
from unittest.mock import patch

# Import tarfile library to extract tarball with udica policy and templates when --ansible
# parameter is used
import tarfile

# Use the selinux and semanage packages provided by the system instead of the mock ones. When
# running on a system with SELinux disabled (e.g. in a container), it must be set to False.
# On RHEL, CentOS or Fedora it may be set to True.
SELINUX_ENABLED = False

# Globally define symbol "udica" so we can override the import
udica = None

DEFAULT_TEMPLATE_STORE = "/usr/share/udica/templates"
TEST_DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def test_file(path):
    return os.path.join(TEST_DIR_PATH, path)


class TestBase(unittest.TestCase):
    """Test basic functionality of udica"""

    @classmethod
    def setUpClass(self):
        if not exists(DEFAULT_TEMPLATE_STORE):
            # download latest policy templates from container-selinux
            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/containers/container-selinux.git",
                        os.path.join(TEST_DIR_PATH, "../", "container-selinux"),
                    ]
                )
            except subprocess.CalledProcessError as e:
                print('Cannot clone "container-selinux" repository: ' + str(e))

    @classmethod
    def tearDownClass(self):
        rmtree(
            os.path.join(TEST_DIR_PATH, "../", "container-selinux"), ignore_errors=True
        )

    def setUp(self):
        # NOTE: We import udica here so the above mocked modules take place.
        global udica
        udica = __import__("udica.__main__")

        # Overwrite paths to files so that they do not have to be installed.
        udica.policy.TEMPLATE_PLAYBOOK = os.path.join(
            TEST_DIR_PATH, "../", "udica/ansible/deploy-module.yml"
        )
        udica.policy.TEMPLATES_STORE = (
            DEFAULT_TEMPLATE_STORE
            if exists(DEFAULT_TEMPLATE_STORE)
            else os.path.join(TEST_DIR_PATH, "../", "container-selinux/udica-templates")
        )
        # FIXME: the policy module is using global variable which must be reset to []
        udica.policy.templates_to_load = []

    def tearDown(self):
        os.unlink("my_container.cil")

        global udica
        udica = None

    def test_basic_podman(self):
        """podman run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_basic.podman.json", "my_container"]
        )
        self.assert_templates(
            output, ["base_container", "net_container", "home_container"]
        )
        self.assert_policy(test_file("test_basic.podman.cil"))

    def test_basic_oci(self):
        """podman run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 ubi8"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_basic.oci.json", "my_container"]
        )
        self.assert_templates(
            output, ["base_container", "net_container", "home_container"]
        )
        self.assert_policy(test_file("test_basic.oci.cil"))

    def test_basic_docker(self):
        """docker run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_basic.docker.json", "my_container"]
        )
        self.assert_templates(
            output, ["base_container", "net_container", "home_container"]
        )
        self.assert_policy(test_file("test_basic.docker.cil"))

    def test_basic_cri(self):
        """Start CRI-O mounting /var/spool with read/write perms and /home and /etc/hosts with readonly perms"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_basic.cri.json",
                "--full-network-access",
                "my_container",
            ]
        )
        self.assert_templates(
            output, ["base_container", "net_container", "home_container"]
        )
        self.assert_policy(test_file("test_basic.cri.cil"))

    def test_basic_specified_engine_cri(self):
        """Start CRI-O mounting /var/spool with read/write perms and /home and /etc/hosts with readonly perms"""
        output = self.run_udica(
            [
                "udica",
                "--container-engine",
                "CRI-O",
                "-j",
                "tests/test_basic.cri.json",
                "--full-network-access",
                "my_container",
            ]
        )
        self.assert_templates(
            output, ["base_container", "net_container", "home_container"]
        )
        self.assert_policy(test_file("test_basic.cri.cil"))

    def test_default_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_default.podman.json", "my_container"]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_default.podman.cil"))

    def test_default_specified_engine_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-e",
                "podman",
                "-j",
                "tests/test_default.podman.json",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_default.podman.cil"))

    def test_default_docker(self):
        """docker run fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_default.docker.json", "my_container"]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_default.docker.cil"))

    def test_default_specified_engine_docker(self):
        """docker run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-e",
                "docker",
                "-j",
                "tests/test_default.docker.json",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_default.docker.cil"))

    def test_default_oci(self):
        """podman run ubi8"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_default.oci.json", "my_container"]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_default.podman.cil"))

    def test_port_ranges_podman(self):
        """podman run -p 63140:63140 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_ports.podman.json", "my_container"]
        )
        self.assert_templates(output, ["base_container", "net_container"])
        self.assert_policy(test_file("test_ports.podman.cil"))

    def test_port_ranges_docker(self):
        """docker run -p 63140:63140 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_ports.docker.json", "my_container"]
        )
        self.assert_templates(output, ["base_container", "net_container"])
        self.assert_policy(test_file("test_ports.docker.cil"))

    def test_default_ansible_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "my_container",
                "--ansible",
            ]
        )
        self.assert_ansible(
            output, ["base_container"], test_file("test_default.ansible.podman.yml")
        )
        self.assert_policy(test_file("test_default.podman.cil"))

    def test_basic_ansible_podman(self):
        """podman run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_basic.podman.json", "my_container", "--ansible"]
        )
        self.assert_ansible(
            output,
            ["base_container", "net_container", "home_container"],
            test_file("test_basic.ansible.podman.yml"),
        )
        self.assert_policy(test_file("test_basic.podman.cil"))

    def test_nocontext_podman(self):
        """podman run -v /tmp/test:/tmp/test:rw fedora"""
        os.makedirs("/tmp/test", exist_ok=True)
        output = self.run_udica(
            ["udica", "-j", "tests/test_nocontext.podman.json", "my_container"]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_nocontext.podman.cil"))
        os.rmdir("/tmp/test")

    def test_stream_connect_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "--stream-connect",
                "network_container",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_stream_connect.podman.cil"))

    def test_fullnetworkaccess_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "--full-network-access",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container", "net_container"])
        self.assert_policy(test_file("test_fullnetworkaccess.podman.cil"))

    def test_virtaccess_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "--virt-access",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container", "virt_container"])
        self.assert_policy(test_file("test_virtaccess.podman.cil"))

    def test_xaccess_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "--X-access",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container", "x_container"])
        self.assert_policy(test_file("test_xaccess.podman.cil"))

    def test_ttyaccess_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "--tty-access",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container", "tty_container"])
        self.assert_policy(test_file("test_ttyaccess.podman.cil"))

    def test_append_more_rules_podman(self):
        """podman run fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_default.podman.json",
                "-a",
                "tests/append_avc_file",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_append_avc.podman.cil"))

    def test_devices_podman(self):
        """podman run --device /dev/fb0 fedora"""
        output = self.run_udica(
            ["udica", "-j", "tests/test_devices.podman.json", "my_container"]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_devices.podman.cil"))

    def test_device_access_podman(self):
        """podman run --device /dev/fb0 fedora"""
        output = self.run_udica(
            [
                "udica",
                "-j",
                "tests/test_devices.podman.json",
                "--devices",
                "/dev/fb0",
                "my_container",
            ]
        )
        self.assert_templates(output, ["base_container"])
        self.assert_policy(test_file("test_devices.podman.cil"))

    # Confined user tests
    def test_confined_user(self):
        """udica confined_user <args> --level s0 --range s0:c0 my_container"""
        for arg in ["cla", "lb", "lsid", "abcdgilmns"]:
            output = self.run_udica(
                [
                    "udica",
                    "confined_user",
                    "-{}".format(arg),
                    "--level",
                    "s0",
                    "--range",
                    "s0:c0",
                    "my_container",
                ],
                True,
            )
            self.assert_policy(test_file("test_confined_{}.cil".format(arg)))

    def run_udica(self, args, confined=False):
        with patch("sys.argv", args):
            with patch("sys.stderr.write") as mock_err, patch(
                "sys.stdout.write"
            ) as mock_out:
                mock_out.output = ""

                def store_output(output):
                    mock_out.output += output

                mock_out.side_effect = store_output
                udica.__main__.main()
                mock_err.assert_not_called()

        if confined:
            self.assertRegex(mock_out.output, "semodule -i my_container.cil")
            self.assertRegex(
                mock_out.output, "semanage login -a -s my_container_u my_container"
            )
        else:
            self.assertRegex(mock_out.output, "Policy my_container created")
            self.assertRegex(
                mock_out.output, "--security-opt label=type:my_container.process"
            )

        return mock_out.output

    def assert_templates(self, output, templates):
        self.assertRegex(output, "semodule -i my_container")
        if templates:
            if len(templates) > 1:
                templ_str = "{%s.cil}" % ".cil,".join(templates)
            else:
                templ_str = templates[0] + ".cil"
            self.assertRegex(output, udica.policy.TEMPLATES_STORE + "/" + templ_str)

    def assert_policy(self, policy_file):
        self.assertTrue(os.path.isfile("my_container.cil"))
        with open("my_container.cil") as cont:
            policy = cont.read().strip()
        with open(policy_file) as cont:
            exp_policy = cont.read().strip()
        self.assertMultiLineEqual(policy, exp_policy)

    def assert_ansible(self, output, templates, variables_file):
        udica.policy.TEMPLATES_STORE = "./"
        self.assertRegex(
            output, "Ansible playbook and archive with udica policies generated!"
        )
        with tarfile.open("my_container-policy.tar.gz") as archive:
            archive.extractall()

        self.assertTrue(os.path.isfile("deploy-module.yml"))

        with open("deploy-module.yml") as cont:
            playbook = cont.read().strip()
        with open(udica.policy.TEMPLATE_PLAYBOOK) as cont:
            exp_playbook = cont.read().strip()
        self.assertMultiLineEqual(playbook, exp_playbook)

        self.assertTrue(os.path.isfile("variables-deploy-module.yml"))

        with open("variables-deploy-module.yml") as cont:
            variables_playbook = cont.read().strip()
        with open(variables_file) as cont:
            exp_variables_playbook = cont.read().strip()
        self.assertMultiLineEqual(variables_playbook, exp_variables_playbook)

        os.unlink("variables-deploy-module.yml")
        os.unlink("my_container-policy.tar.gz")
        os.unlink("deploy-module.yml")

        for temp in templates:
            os.unlink(temp + ".cil")
