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
import sys
import unittest
import importlib
from unittest.mock import patch

sys.path.insert(0, os.path.abspath('..'))
import udica.__main__

class TestMain(unittest.TestCase):
    """Test basic functionality of udica"""

    def test_basic_podman(self):
        """podman run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora"""
        args = ['udica', '-j', 'test_basic.podman.json', 'my_container']
        self.helper(args, 'test_basic.podman.cil',
                    '{base_container.cil,net_container.cil,home_container.cil}')

    def test_basic_docker(self):
        """docker run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora"""
        args = ['udica', '-j', 'test_basic.docker.json', 'my_container']
        self.helper(args, 'test_basic.docker.cil',
                    '{base_container.cil,net_container.cil,home_container.cil}')

    def test_default_podman(self):
        """podman run fedora"""
        args = ['udica', '-j', 'test_default.podman.json', 'my_container']
        self.helper(args, 'test_default.podman.cil', 'base_container.cil')

    def test_default_docker(self):
        """docker run fedora"""
        args = ['udica', '-j', 'test_default.docker.json', 'my_container']
        self.helper(args, 'test_default.docker.cil', 'base_container.cil')

    def test_port_ranges_podman(self):
        """podman run -p 63140:63140 fedora"""
        args = ['udica', '-j', 'test_ports.podman.json', 'my_container']
        self.helper(args, 'test_ports.podman.cil', '{base_container.cil,net_container.cil}')

    def test_port_ranges_docker(self):
        """docker run -p 63140:63140 fedora"""
        args = ['udica', '-j', 'test_ports.docker.json', 'my_container']
        self.helper(args, 'test_ports.docker.cil', '{base_container.cil,net_container.cil}')

    def helper(self, args, policy_file=None, templates=None):
        """Run udica with args, check output and used templates.

        Arguments:
        args -- list of program arguments (the first one is an executable name)
        policy_file -- check that output of udica matches this file
        templates -- check that these templates are part of udica output, e.g. 'base_container.cil'
            or '{base_container.cil,net_container.cil}'
        """
        udica.policy.TEMPLATES_STORE = "../udica/templates"
        # FIXME: the policy module is using global variable which must be reset to []
        udica.policy.templates_to_load = []
        # FIXME: the load_policy function is not properly restoring current working directory
        self.cwd = os.getcwd()

        import selinux
        importlib.reload(selinux)
        import semanage
        importlib.reload(semanage)

        with patch('sys.argv', args):
            with patch('sys.stderr.write') as mock_err, patch('sys.stdout.write') as mock_out:
                mock_out.output = ""
                def store_output(output):
                    mock_out.output += output
                mock_out.side_effect = store_output
                udica.__main__.main()
                mock_err.assert_not_called()

        self.assertRegex(mock_out.output, 'Policy my_container created')
        self.assertRegex(mock_out.output, '--security-opt label=type:my_container.process')
        self.assertRegex(mock_out.output, 'semodule -i my_container')

        if templates:
            self.assertRegex(mock_out.output, udica.policy.TEMPLATES_STORE + '/' + templates)

        os.chdir(self.cwd)

        self.assertTrue(os.path.isfile('my_container.cil'))

        if policy_file:
            with open('my_container.cil') as cont:
                policy = cont.read().strip()
            with open(policy_file) as cont:
                exp_policy = cont.read().strip()
            self.assertMultiLineEqual(policy, exp_policy)

        os.unlink('my_container.cil')
