#!/bin/python3

import selinux
import semanage

import perms

config_container = '/etc'
home_container = '/home'
log_container = '/var/log'
tmp_container = '/tmp'

def list_contexts(directory):
    directory_len = (len(directory))

    handle = semanage.semanage_handle_create()
    semanage.semanage_connect(handle)

    (rc, fclist) = semanage.semanage_fcontext_list(handle)
    (rc, fclocal) = semanage.semanage_fcontext_list_local(handle)
    (rc, fchome) = semanage.semanage_fcontext_list_homedirs(handle)

    contexts = []
    for fcontext in fclist + fclocal + fchome:
        # print(semanage.semanage_fcontext_get_expr(fcontext))
        expression = semanage.semanage_fcontext_get_expr(fcontext)
        if expression[0:directory_len] == directory:
            contexts.append(semanage.semanage_context_get_type(semanage.semanage_fcontext_get_con(fcontext)))
    selabel = selinux.selabel_open(selinux.SELABEL_CTX_FILE, None, 0)
    (rc, context) = selinux.selabel_lookup(selabel, directory, 0)
    contexts.append(context.split(':')[2])
    return contexts

def list_ports(port_number):

    handle = semanage.semanage_handle_create()
    semanage.semanage_connect(handle)

    (rc, plist) = semanage.semanage_port_list(handle)
    (rc, plocal) = semanage.semanage_port_list_local(handle)

    for port in plist + plocal:
        con = semanage.semanage_port_get_con(port)
        ctype = semanage.semanage_context_get_type(con)
        low = semanage.semanage_port_get_low(port)
        if (low == port_number):
            return ctype

def create_policy(opts,capabilities,mounts,ports):
    policy = open(opts['ContainerName'] +'.cil', 'w')
    policy.write('(block ' + opts['ContainerName'] + '\n')
    policy.write('    (blockinherit container)\n')

    if opts['FullNetworkAccess']:
        policy.write('    (blockinherit net_container)\n')

    if ports:
        policy.write('    (blockinherit restricted_net_container)\n')

    # capabilities
    caps=''
    for item in capabilities:
        caps = caps + perms.cap[item]

    policy.write('    (allow process process ( capability ( ' + caps  + '))) \n')
    policy.write('\n')

    # ports
    for item in ports:
        policy.write('    (allow process ' + list_ports(item['hostPort']) + ' ( ' + perms.socket[item['protocol']] + ' (  name_bind ))) \n')

    # mounts
    for item in mounts:
        if not item['source'].find("/"):
            if (item['source'] == log_container and 'ro' in item['options']):
                policy.write('    (blockinherit log_container)\n')
                continue;

            if (item['source'] == log_container and 'rw' in item['options']):
                policy.write('    (blockinherit log_rw_container)\n')
                continue;

            if (item['source'] == home_container and 'ro' in item['options']):
                policy.write('    (blockinherit home_container)\n')
                continue;

            if (item['source'] == home_container and 'rw' in item['options']):
                policy.write('    (blockinherit home_rw_container)\n')
                continue;

            if (item['source'] == tmp_container and 'ro' in item['options']):
                policy.write('    (blockinherit tmp_container)\n')
                continue;

            if (item['source'] == tmp_container and 'rw' in item['options']):
                policy.write('    (blockinherit tmp_rw_container)\n')
                continue;

            if (item['source'] == config_container and 'ro' in item['options']):
                policy.write('    (blockinherit config_container)\n')
                continue;

            if (item['source'] == config_container and 'rw' in item['options']):
                policy.write('    (blockinherit config_rw_container)\n')
                continue;

            contexts = list_contexts(item['source'])
            for context in contexts:
                if 'rw' in item['options']:
                    policy.write('    (allow process ' + context + ' ( dir ( ' + perms.perm['drw'] + ' ))) \n')
                    policy.write('    (allow process ' + context + ' ( file ( ' + perms.perm['frw'] + ' ))) \n')
                    policy.write('    (allow process ' + context + ' ( sock_file ( ' + perms.perm['srw'] + ' ))) \n')
                if 'ro' in item['options']:
                    policy.write('    (allow process ' + context + ' ( dir ( ' + perms.perm['dro'] + ' ))) \n')
                    policy.write('    (allow process ' + context + ' ( file ( ' + perms.perm['fro'] + ' ))) \n')
                    policy.write('    (allow process ' + context + ' ( sock_file ( ' + perms.perm['sro'] + ' ))) \n')

    policy.write(') ')
    policy.close()
