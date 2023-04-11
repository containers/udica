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

from unittest.mock import Mock

SELABEL_CTX_FILE = None

selabel_open = Mock()


def selabel_lookup(selabel, directory, rc):
    if directory == "/tmp/test":
        return (0, None)
    elif directory == "/dev/fb0":
        return (0, "system_u:object_r:framebuf_device_t:s0")
    elif directory == "/etc/hosts":
        return (0, "system_u:object_r:net_conf_t:s0")
    else:
        return (0, "system_u:object_r:var_spool_t:s0")


def getfilecon(directory):
    if directory == "/tmp/test":
        return (0, "system_u:object_r:user_tmp_t:s0")
    elif directory == "/etc/hosts":
        return (0, "system_u:object_r:net_conf_t:s0")
    else:
        return (0, "system_u:object_r:var_spool_t:s0")
