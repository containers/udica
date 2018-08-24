# Container SELinux Customization

This repository contains a proof of concept demonstrating block inheritance via CIL namespaces, which allows better container separation.

### Prerequisites

Container engine (e.g: podman) and sesearch tool for searching SELinux rules need to be installed on your system.

    # dnf install podman setools-console
    # dnf remove -y container-selinux

### Installing

    $ cd container-selinux-customization

    # make

    # semodule -i container_runtime.pp
    # semodule -i container.cil
    # semodule -i net_container.cil
    # semodule -i home_container.cil

Make sure that SELinux is in Enforcing mode

    # setenforce 1
    # getenforce
    Enforcing

## Examples

### Home directory access

The following command will run the latest system fedora container in container.process domain (alias for container_t), which is general type for containers shipped in container-selinux package.

    $ cat my_container.cil
    (block my_container
	    (blockinherit container)
    )

    # semodule -i my_container.cil

    # podman run -v /home:/home --security-opt label=type:my_container.process -i -t fedora bash
    [root@2578c94cdd73 /]# cd /home
    [root@2578c94cdd73 home]# ls
    ls: cannot open directory '.': Permission denied


Note: container namespace *CANNOT* access home_root_t dirs/objests so sesearch won't find any allow rule related to this access

    # sesearch -A -s my_container.process -t home_root_t

However, home_container.cil inherits rules from container namespace and adds several new rules to access /home dir

    $ cat my_container.cil
    (block my_container
	    (blockinherit home_container)
    )

    # semodule -i my_container.cil

    # sesearch -A -s my_container.process -t home_root_t
    allow my_container.process home_root_t:dir { getattr ioctl lock open read search };

    # podman run -v /home:/home --security-opt label=type:my_container.process -i -t fedora bash
    [root@0469dc13f1a8 /]# cd /home
    [root@0469dc13f1a8 home]# ls
    lvrabec

home_container.cil file provides also home_rw_container and home_manage_container for granting more permissions to confined container.

    $ cat my_container.cil
    (block my_container
	    (blockinherit home_rw_container)
    )

    # semodule -i my_container.cil

    # sesearch -A -s my_container.process -t home_root_t
    allow my_container.process home_root_t:dir { add_name getattr ioctl link lock open read remove_name reparent search setattr write };

    $ cat my_container.cil
    (block my_container
	    (blockinherit home_manage_container)
    )

    # semodule -i my_container.cil
    # allow my_container.process home_root_t:dir { add_name create getattr ioctl link lock open read remove_name rename reparent rmdir search setattr unlink write };

### Network access

The next example will explain the difference between generic container.process label and net_container. net_container inherits rules from container namespace and additionally allows network access.

    $ cat my_container.cil
    (block my_container
	    (blockinherit container)
    )

    # semodule -i my_container.cil

    # podman run --security-opt label=type:my_container.process -i -t fedora bash
    [root@ed342fdb6e42 /]# dnf check-update
    Error: Failed to synchronize cache for repo 'updates'

Note: container namespace *CANNOT* access http_port_t ports so sesearch won't find any allow rule related to this access

    # sesearch -A -s my_container.process -t http_port_t -c tcp_socket

With net_container namespace we're able to connect to network and check for updates.

    $ cat my_container.cil
    (block my_container
	    (blockinherit net_container)
    )

    # semodule -i my_container.cil

    # podman run --security-opt label=type:my_container.process -i -t fedora bash
    [root@ed342fdb6e42 /]# dnf check-update
    Fedora 27 - x86_64 - Updates                                              66 MB/s |  22 MB     00:00
    Fedora 27 - x86_64                                                        61 MB/s |  58 MB     00:00
    Last metadata expiration check: 0:00:07 ago on Sun Apr 15 19:49:27 2018.
    ...


The following SELinux query confirms that my_container.process can access http_port_t

    # sesearch -A -s my_container.process -t http_port_t -c tcp_socket
    allow sandbox_net_domain port_type:tcp_socket { name_bind name_connect recv_msg send_msg };

### Log reader container

The following container SELinux policy template will allow container read logs stored under /var/log.

    $ cat logreader_container.cil
    (block logreader_container
        (blockinherit container)
        (allow process var_t (dir (getattr search open)))
        (allow process logfile (dir (ioctl read getattr lock search open)))
        (allow process logfile (file (ioctl read getattr lock open map)))
        (allow process auditd_log_t (dir (ioctl read getattr lock search open)))
        (allow process auditd_log_t (file (ioctl read getattr lock open)))
    )

    # semodule -i logreader_container.cil

    # podman run -v /var/log:/var/log --security-opt label=type:logreader_container.process -i -t fedora bash
    # [root@fdc97ba59f66 /]# cd /var/log
    # [root@fdc97ba59f66 log]# ls
    ...

For testing purposes, basic container policy do not allowing access to /var/log/

    # podman run -v /var/log:/var/log --security-opt label=type:container.process -i -t fedora bash
    [root@ffb8b43e7d9e /]# cd /var/log/
    [root@ffb8b43e7d9e /]# ls
    ls: cannot open directory '.': Permission denied

### Merging 

Let's say, that you would like to merge net_container and home_container namespace to allow network access and also access to homedirs.
There is a way to merge namespaces.

    $ cat my_container.cil
    (block my_container
	    (blockinherit home_rw_container)
	    (blockinherit net_container)
    )

    # semodule -i my_container.cil

Now, namespaces are merged, following sesearch queries confirms it.

    $ sesearch -A -s my_container.process -t home_root_t 
    allow my_container.process home_root_t:dir { add_name getattr ioctl link lock open read remove_name reparent search setattr write };

    $ sesearch -A -s my_container.process -t http_port_t -c tcp_socket 
    allow sandbox_net_domain port_type:tcp_socket { name_bind name_connect recv_msg send_msg };

### Fluentd container

Currently, fluentd Pods run as super privileged container, and this is too permisive.  The fluentd pod needs to be able to read the hosts /var/log among others mount points. The previous enforces to run the FluentD containers with the "privileged: true" flag which causes containers to run with "spc_t" selinux policy which is too permissive (It's unconfined from SELinux POV). Following policy brings tighten security to fluend pods:

    $ cat fluentd_container.cil
    (block fluentd_container
    (blockinherit net_container)
    (blockinherit logreader_container)
    (allow process process (capability (fowner chown setgid setuid)))
    )

    $ semodule -i fluentd_container.cil

    # podman run -v /var/log:/var/log --security-opt label=type:fluentd_container.process -i -t fluent/fluentd
    2018-07-25 11:46:00 +0000 [info]: parsing config file is succeeded path="/fluentd/etc/fluent.conf"
    2018-07-25 11:46:00 +0000 [warn]: [output_docker1] 'time_format' specified without 'time_key', will be ignored
    2018-07-25 11:46:00 +0000 [warn]: [output1] 'time_format' specified without 'time_key', will be ignored
    2018-07-25 11:46:00 +0000 [info]: using configuration file: <ROOT>
    ...
