# Copyright (C) 2018 Lukas Vrabec, <lvrabec@redhat.com>
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

perm = {
    "devrw": "getattr read write append ioctl lock open",
    "drw": "add_name create getattr ioctl lock open read remove_name rmdir search setattr write",
    "dro": "getattr ioctl lock open read search",
    "frw": "append create getattr ioctl lock map open read rename setattr unlink write",
    "fro": "getattr ioctl lock open read",
    "srw": "append getattr open read write",
    "sro": "getattr open read",
}

socket = {"tcp": "tcp_socket", "udp": "udp_socket", "sctp": "sctp_socket"}
