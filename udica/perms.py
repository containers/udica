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

cap = {
        'CHOWN':'chown ',
        'DAC_OVERRIDE':'dac_override ',
        'DAC_READ_SEARCH':'dac_read_search ',
        'FOWNER':'fowner ',
        'FSETID':'fsetid ',
        'KILL':'kill ',
        'SETGID':'setgid ',
        'SETUID':'setuid ',
        'SETPCAP':'setpcap ',
        'LINUX_IMMUTABLE':'linux_immutable ',
        'NET_BIND_SERVICE':'net_bind_service ',
        'NET_BROADCAST':'net_broadcast ',
        'NET_ADMIN':'net_admin ',
        'NET_RAW':'net_raw ',
        'IPC_LOCK':'ipc_lock ',
        'IPC_OWNER':'ipc_owner ',
        'SYS_MODULE':'sys_module ',
        'SYS_RAWIO':'sys_rawio ',
        'SYS_CHROOT':'sys_chroot ',
        'SYS_PTRACE':'sys_ptrace ',
        'SYS_PACCT':'sys_pacct ',
        'SYS_ADMIN':'sys_admin ',
        'SYS_BOOT':'sys_boot ',
        'SYS_NICE':'sys_nice ',
        'SYS_RESOURCE':'sys_resource ',
        'SYS_TIME':'sys_time ',
        'SYS_TTY_CONFIG':'sys_tty_config ',
        'MKNOD':'mknod ',
        'LEASE':'lease ',
        'AUDIT_WRITE':'audit_write ',
        'AUDIT_CONTROL':'audit_control ',
        'SETFCAP':'setfcap ',
        'MAC_OVERRIDE':'mac_override ',
        'MAC_ADMIN':'mac_admin ',
        'SYSLOG':'syslog ',
        'WAKE_ALARM':'wake_alarm ',
        'BLOCK_SUSPEND':'block_suspend ',
        'AUDIT_READ':'audit_read '
}

perm = {
        'drw': 'open read getattr lock search ioctl add_name remove_name write',
        'dro': 'getattr search open read lock ioctl',
        'frw': 'getattr read write append ioctl lock map open create ',
        'fro': 'getattr read ioctl lock open ',
        'srw': 'getattr read write append open ',
        'sro': 'getattr read open ',
}

socket = {
        'tcp': 'tcp_socket',
        'udp': 'udp_socket',
}
