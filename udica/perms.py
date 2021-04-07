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
    "device_rw": "getattr read write append ioctl lock open",
    "dir_rw": "add_name create getattr ioctl lock open read remove_name rmdir search setattr write",
    "dir_ro": "getattr ioctl lock open read search",
    "file_rw": "append create getattr ioctl lock map open read rename setattr unlink write",
    "file_ro": "getattr ioctl lock open read",
    "fifo_rw": "getattr read write append ioctl lock open",
    "fifo_ro": "getattr open read lock ioctl",
    "socket_rw": "append getattr open read write",
    "socket_ro": "getattr open read",
}

socket = {"tcp": "tcp_socket", "udp": "udp_socket", "sctp": "sctp_socket"}
