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
from unittest.mock import patch

import tests.test_main
import tests.selinux as mocked_selinux
import tests.semanage as mocked_semanage


class TestUnit(tests.test_main.TestBase):
    """Test basic functionality of udica"""

    def setUp(self):
        self.selinux_patch = patch.dict("sys.modules", selinux=mocked_selinux)
        self.selinux_patch.start()

        self.semanage_patch = patch.dict("sys.modules", semanage=mocked_semanage)
        self.semanage_patch.start()

        super().setUp()

    def tearDown(self):
        self.selinux_patch.stop()
        self.semanage_patch.stop()
        super().tearDown()
