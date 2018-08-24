#!/bin/python3

import selinux
import semanage

import perms

def ListContexts(directory):
    directory_len = (len(directory))

    handle = semanage.semanage_handle_create()
    semanage.semanage_connect(handle)

    (rc, fclist) = semanage.semanage_fcontext_list(handle)
    (rc, fclocal) = semanage.semanage_fcontext_list_local(handle)
    (rc, fchome) = semanage.semanage_fcontext_list_homedirs(handle)

    Contexts = []
    for fcontext in fclist + fclocal + fchome:
        # print(semanage.semanage_fcontext_get_expr(fcontext))
        expression = semanage.semanage_fcontext_get_expr(fcontext)
        if expression[0:directory_len] == directory:
            Contexts.append(semanage.semanage_context_get_type(semanage.semanage_fcontext_get_con(fcontext)))
    selabel = selinux.selabel_open(selinux.SELABEL_CTX_FILE, None, 0)
    (rc, context) = selinux.selabel_lookup(selabel, directory, 0)
    Contexts.append(context.split(':')[2])
    return Contexts

def CreatePolicy(opts,capabilities,mounts):
    policy = open(opts['ContainerName'] +'.cil', 'w')
    policy.write('(block ' + opts['ContainerName'] + '\n')
    policy.write('    (blockinherit container)\n')

    caps=''
    for item in capabilities:
        caps = caps + perms.cap[item]

    policy.write('    (allow process process ( capability ( ' + caps  + '))) \n')
    policy.write('\n')

    for item in mounts:
        if not item['source'].find("/"):
            Contexts = ListContexts(item['source'])
            for context in Contexts:
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
