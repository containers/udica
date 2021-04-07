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

semanage_handle_create = Mock()
semanage_connect = Mock()
semanage_context_get_type = Mock(side_effect=lambda x: x.split(":")[2])

ports = [
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 1, 1),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 1, 1),
    ("system_u:object_r:echo_port_t:s0", "tcp", 7, 7),
    ("system_u:object_r:echo_port_t:s0", "tcp", 7, 7),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 9, 9),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 9, 9),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 13, 13),
    # default ranges
    ("system_u:object_r:reserved_port_t:s0", "udp", 1, 511),
    ("system_u:object_r:reserved_port_t:s0", "tcp", 1, 511),
    ("system_u:object_r:reserved_port_t:s0", "sctp", 1, 511),
    ("system_u:object_r:hi_reserved_port_t:s0", "udp", 512, 1023),
    ("system_u:object_r:hi_reserved_port_t:s0", "tcp", 512, 1023),
    ("system_u:object_r:hi_reserved_port_t:s0", "sctp", 512, 1023),
    ("system_u:object_r:unreserved_port_t:s0", "udp", 61001, 65535),
    ("system_u:object_r:unreserved_port_t:s0", "tcp", 61001, 65535),
    ("system_u:object_r:ephemeral_port_t:s0", "udp", 32768, 60999),
    ("system_u:object_r:ephemeral_port_t:s0", "tcp", 32768, 60999),
    ("system_u:object_r:unreserved_port_t:s0", "udp", 1024, 32767),
    ("system_u:object_r:unreserved_port_t:s0", "tcp", 1024, 32767),
    ("system_u:object_r:unreserved_port_t:s0", "sctp", 1024, 65535),
]
ports_local = [
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 13, 13),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 19, 19),
    ("system_u:object_r:inetd_child_port_t:s0", "tcp", 19, 19),
    ("system_u:object_r:ftp_data_port_t:s0", "tcp", 20, 20),
    ("system_u:object_r:ftp_port_t:s0", "tcp", 21, 21),
    ("system_u:object_r:mysqld_port_t:s0", "tcp", 63132, 63164),
]
semanage_port_list = Mock(return_value=(0, ports))
semanage_port_list_local = Mock(return_value=(0, ports_local))
semanage_port_get_con = Mock(side_effect=lambda x: x[0])
semanage_port_get_proto = Mock(side_effect=lambda x: x[1])
semanage_port_get_proto_str = Mock(side_effect=lambda x: x)
semanage_port_get_low = Mock(side_effect=lambda x: x[2])
semanage_port_get_high = Mock(side_effect=lambda x: x[3])

fcontexts = [
    ("/var/spool(/.*)?", "system_u:object_r:var_spool_t:s0"),
    ("/var/spool/[mg]dm(/.*)?", "system_u:object_r:xdm_spool_t:s0"),
    ("/var/spool/(client)?mqueue(/.*)?", "system_u:object_r:mqueue_spool_t:s0"),
    ("/var/spool/(.*/)?a?quota\\.(user|group)", "system_u:object_r:quota_db_t:s0"),
    ("/var/spool/at(/.*)?", "system_u:object_r:user_cron_spool_t:s0"),
    ("/var/spool/faf(/.*)?", "system_u:object_r:abrt_retrace_spool_t:s0"),
    ("/var/spool/fax(/.*)?", "system_u:object_r:getty_var_run_t:s0"),
    ("/var/spool/lpd(/.*)?", "system_u:object_r:print_spool_t:s0"),
    ("/var/spool/sms(/.*)?", "system_u:object_r:smsd_spool_t:s0"),
    ("/var/spool/abrt(/.*)?", "system_u:object_r:abrt_var_cache_t:s0"),
    ("/var/spool/ctdb(/.*)?", "system_u:object_r:ctdbd_spool_t:s0"),
    ("/var/spool/cups(/.*)?", "system_u:object_r:print_spool_t:s0"),
    ("/var/spool/gosa(/.*)?", "system_u:object_r:httpd_sys_rw_content_t:s0"),
    ("/var/spool/imap(/.*)?", "system_u:object_r:mail_spool_t:s0"),
    ("/var/spool/mail(/.*)?", "system_u:object_r:mail_spool_t:s0"),
    ("/var/spool/news(/.*)?", "system_u:object_r:news_spool_t:s0"),
    ("/var/spool/rwho(/.*)?", "system_u:object_r:rwho_spool_t:s0"),
    ("/var/spool/uucp(/.*)?", "system_u:object_r:uucpd_spool_t:s0"),
    ("/var/spool/exim[0-9]?(/.*)?", "system_u:object_r:exim_spool_t:s0"),
    ("/var/spool/audit(/.*)?", "system_u:object_r:audit_spool_t:s0"),
    ("/var/spool/debug(/.*)?", "system_u:object_r:abrt_var_cache_t:s0"),
    ("/var/spool/samba(/.*)?", "system_u:object_r:samba_spool_t:s0"),
    ("/var/spool/smtpd(/.*)?", "system_u:object_r:mail_spool_t:s0"),
    ("/var/spool/spamd(/.*)?", "system_u:object_r:spamd_spool_t:s0"),
    ("/var/spool/squid(/.*)?", "system_u:object_r:squid_cache_t:s0"),
    ("/var/spool/texmf(/.*)?", "system_u:object_r:tetex_data_t:s0"),
    ("/var/spool/voice(/.*)?", "system_u:object_r:getty_var_run_t:s0"),
    ("/var/spool/bacula.*", "system_u:object_r:bacula_spool_t:s0"),
    ("/var/spool/icinga(/.*)?", "system_u:object_r:nagios_spool_t:s0"),
    ("/var/spool/nagios(/.*)?", "system_u:object_r:nagios_spool_t:s0"),
    ("/var/spool/snmptt(/.*)?", "system_u:object_r:snmpd_var_lib_t:s0"),
    ("/var/spool/spampd(/.*)?", "system_u:object_r:spamd_spool_t:s0"),
    ("/var/spool/viewvc(/.*)?", "system_u:object_r:httpd_sys_rw_content_t:s0"),
    ("/var/spool/cron/a?quota\\.(user|group)", "system_u:object_r:quota_db_t:s0"),
    ("/var/spool/mailman.*", "system_u:object_r:mailman_data_t:s0"),
    ("/var/spool/postfix.*", "system_u:object_r:postfix_spool_t:s0"),
    ("/var/spool/amavisd(/.*)?", "system_u:object_r:antivirus_db_t:s0"),
    ("/var/spool/anacron(/.*)?", "system_u:object_r:system_cron_spool_t:s0"),
    ("/var/spool/courier(/.*)?", "system_u:object_r:courier_spool_t:s0"),
    ("/var/spool/dovecot(/.*)?", "system_u:object_r:dovecot_spool_t:s0"),
    ("/var/spool/prelude(/.*)?", "system_u:object_r:prelude_spool_t:s0"),
    ("/var/spool/pyicq-t(/.*)?", "system_u:object_r:pyicqt_var_spool_t:s0"),
    ("/var/spool/rsyslog(/.*)?", "system_u:object_r:var_log_t:s0"),
    ("/var/spool/up2date(/.*)?", "system_u:object_r:rpm_var_cache_t:s0"),
    ("/var/spool/asterisk(/.*)?", "system_u:object_r:asterisk_spool_t:s0"),
    ("/var/spool/cups-pdf(/.*)?", "system_u:object_r:print_spool_t:s0"),
    ("/var/spool/opendkim(/.*)?", "system_u:object_r:dkim_milter_data_t:s0"),
    ("/var/spool/plymouth(/.*)?", "system_u:object_r:plymouthd_spool_t:s0"),
    ("/var/spool/mqueue\\.in(/.*)?", "system_u:object_r:mqueue_spool_t:s0"),
    ("/var/spool/opendmarc(/.*)?", "system_u:object_r:dkim_milter_data_t:s0"),
    ("/var/spool/MIMEDefang(/.*)?", "system_u:object_r:spamd_var_run_t:s0"),
    ("/var/spool/authdaemon(/.*)?", "system_u:object_r:courier_spool_t:s0"),
    ("/var/spool/bacula/log(/.*)?", "system_u:object_r:var_log_t:s0"),
    ("/var/spool/callweaver(/.*)?", "system_u:object_r:callweaver_spool_t:s0"),
    ("/var/spool/gridengine(/.*)?", "system_u:object_r:sge_spool_t:s0"),
    ("/var/spool/rhsm/debug(/.*)?", "system_u:object_r:abrt_var_cache_t:s0"),
    ("/var/spool/turboprint(/.*)?", "system_u:object_r:lpd_var_run_t:s0"),
    ("/var/spool/uucppublic(/.*)?", "system_u:object_r:uucpd_spool_t:s0"),
    ("/var/spool/MailScanner(/.*)?", "system_u:object_r:mscan_spool_t:s0"),
    ("/var/spool/abrt-upload(/.*)?", "system_u:object_r:public_content_rw_t:s0"),
    ("/var/spool/postfix/etc(/.*)?", "system_u:object_r:etc_t:s0"),
    ("/var/spool/postfix/lib(/.*)?", "system_u:object_r:lib_t:s0"),
    ("/var/spool/postfix/usr(/.*)?", "system_u:object_r:lib_t:s0"),
    ("/var/spool/postfix/pid/.*", "system_u:object_r:postfix_var_run_t:s0"),
    ("/var/spool/abrt-retrace(/.*)?", "system_u:object_r:abrt_retrace_spool_t:s0"),
    ("/var/spool/milter-regex(/.*)?", "system_u:object_r:regex_milter_data_t:s0"),
    ("/var/spool/spamassassin(/.*)?", "system_u:object_r:spamd_spool_t:s0"),
    ("/var/spool/squirrelmail(/.*)?", "system_u:object_r:squirrelmail_spool_t:s0"),
    ("/var/spool/MD-Quarantine(/.*)?", "system_u:object_r:spamd_var_run_t:s0"),
    ("/var/spool/postfix/defer(/.*)?", "system_u:object_r:postfix_spool_t:s0"),
    ("/var/spool/postfix/flush(/.*)?", "system_u:object_r:postfix_spool_t:s0"),
    ("/var/spool/postfix/lib64(/.*)?", "system_u:object_r:lib_t:s0"),
    ("/var/spool/postfix/bounce(/.*)?", "system_u:object_r:postfix_spool_bounce_t:s0"),
    ("/var/spool/postfix/public(/.*)?", "system_u:object_r:postfix_public_t:s0"),
    ("/var/spool/retrace-server(/.*)?", "system_u:object_r:abrt_retrace_spool_t:s0"),
    ("/var/spool/postfix/lib/ld.*\\.so.*", "system_u:object_r:ld_so_t:s0"),
    ("/var/spool/postfix/private(/.*)?", "system_u:object_r:postfix_private_t:s0"),
    ("/var/spool/postfix/spamass(/.*)?", "system_u:object_r:spamass_milter_data_t:s0"),
    ("/var/spool/prelude-manager(/.*)?", "system_u:object_r:prelude_spool_t:s0"),
    ("/var/spool/postfix/deferred(/.*)?", "system_u:object_r:postfix_spool_t:s0"),
    ("/var/spool/postfix/maildrop(/.*)?", "system_u:object_r:postfix_spool_t:s0"),
    ("/var/spool/postfix/postgrey(/.*)?", "system_u:object_r:postgrey_spool_t:s0"),
    ("/var/log/boot\.log.*", "system_u:object_r:plymouthd_var_log_t:s0"),
    ("/var/spool/plymouth/boot\.log.*", "system_u:object_r:plymouthd_var_log_t:s0"),
    ("/var/spool/zoneminder-upload(/.*)?", "system_u:object_r:zoneminder_spool_t:s0"),
]
fcontexts_local = [
    ("/var/spool/cron", "system_u:object_r:user_cron_spool_t:s0"),
    ("/var/spool/fcron", "system_u:object_r:cron_spool_t:s0"),
    ("/var/spool/postfix/dev", "system_u:object_r:device_t:s0"),
    ("/var/spool/postfix/pid", "system_u:object_r:var_run_t:s0"),
    ("/var/spool/fcron/systab", "system_u:object_r:system_cron_spool_t:s0"),
]
fcontexts_homedirs = [
    ("/var/spool/cron/crontabs", "system_u:object_r:cron_spool_t:s0"),
    ("/var/spool/postfix/dev/log", "system_u:object_r:devlog_t:s0"),
    ("/var/spool/fcron/new\\.systab", "system_u:object_r:system_cron_spool_t:s0"),
    ("/var/spool/fcron/systab\\.orig", "system_u:object_r:system_cron_spool_t:s0"),
    ("/var/spool/postfix/etc/localtime", "system_u:object_r:locale_t:s0"),
    ("/var/spool/cron/user", "system_u:object_r:user_cron_spool_t:s0"),
    ("/var/spool/cron/[^/]+", "system_u:object_r:user_cron_spool_t:s0"),
]

semanage_fcontext_list = Mock(return_value=(0, fcontexts))
semanage_fcontext_list_local = Mock(return_value=(0, fcontexts_local))
semanage_fcontext_list_homedirs = Mock(return_value=(0, fcontexts_homedirs))
semanage_fcontext_get_expr = Mock(side_effect=lambda x: x[0])
semanage_fcontext_get_con = Mock(side_effect=lambda x: x[1])
