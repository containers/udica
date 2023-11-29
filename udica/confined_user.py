# Copyright (C) 2023 Vit Mojzis, <vmojzis@redhat.com>
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation; either version 2 of
#    the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.

MACRO_CALLS = {
    "admin_commands": (
        "(call confinedom_admin_commands_macro ({}))",
        ("_t", "_r", "_sudo_t"),
    ),
    "graphical_login": (
        "(call confinedom_graphical_login_macro ({}))",
        ("_t", "_r", "_dbus_t"),
    ),
    "mozilla_usage": ("(call confinedom_mozilla_usage_macro ({}))", ("_t", "_r")),
    "networking": ("(call confinedom_networking_macro ({}))", ("_t", "_r")),
    "security_advanced": (
        "(call confinedom_security_advanced_macro ({}))",
        ("_t", "_r", "_sudo_t", "_userhelper_t"),
    ),
    "security_basic": ("(call confinedom_security_basic_macro ({}))", ("_t", "_r")),
    "sudo": (
        "(call confinedom_sudo_macro ({}))",
        ("_t", "_r", "_sudo_t", "_sudo_tmp_t"),
    ),
    "user_login": (
        "(call confinedom_user_login_macro ({}))",
        ("_t", "_r", "_gkeyringd_t", "_dbus_t", "_exec_content"),
    ),
    "ssh_connect": (
        "(call confined_ssh_connect_macro ({}))",
        ("_t", "_r", "_ssh_agent_t"),
    ),
    "basic_commands": ("(call confined_use_basic_commands_macro ({}))", ("_t", "_r")),
}

TYPE_DEFS = {
    "_t": "(type {}_t)",
    "_r": "(role {}_r)",
    "_dbus_t": "(type {}_dbus_t)",
    "_gkeyringd_t": "(type {}_gkeyringd_t)",
    "_ssh_agent_t": "(type {}_ssh_agent_t)",
    "_sudo_t": "(type {}_sudo_t)",
    "_sudo_tmp_t": "(type {}_sudo_tmp_t)",
    "_userhelper_t": "(type {}_userhelper_t)",
    "_exec_content": "(boolean {}_exec_content true)",
}


def create_confined_user_policy(opts):
    # MCS/MLS range handling - needs to be separated into up-to 4 parts
    # s0-s15:c0.c1023 ->  (userrange {uname}_u ((s0 ) (s15 (range c0 c1023))))
    # s0:c0 ->  (userrange {uname}_u ((s0 ) (s0 (c0))))
    mls_range = opts["range"]
    mcs_range = ""
    # separate MCS portion
    if ":" in opts["range"]:
        # s0:c0.c1023
        (mls_range, mcs_range) = opts["range"].split(":")
    if "-" in mls_range:
        # s0-s15
        (range_l, range_h) = mls_range.split("-")
    else:
        # s0
        range_l = mls_range
        range_h = range_l
    if mcs_range != "":
        if "." in mcs_range:
            # s0:c0.c1023 -> (userrange {uname}_u ((s0 ) (s0 (range c0 c1023))))
            (mcs_range_l, mcs_range_h) = mcs_range.split(".")
            mcs_range = "(range {} {})".format(mcs_range_l, mcs_range_h)
        else:
            # s0:c0 -> (userrange {uname}_u ((s0 ) (s0 (c0))))
            mcs_range = "({})".format(mcs_range)

    range = "({} ) ({} {})".format(range_l, range_h, mcs_range)

    defs = set()

    policy = """
(user {uname}_u)
(userrole {uname}_u {uname}_r)
(userlevel {uname}_u ({level}))
(userrange {uname}_u ({range}))
""".format(
        uname=opts["uname"], level=opts["level"], range=range
    )

    # process arguments determining which macros are to be used
    for arg, value in opts.items():
        if not value or arg not in MACRO_CALLS.keys():
            continue
        for param in MACRO_CALLS[arg][1]:
            defs.add(TYPE_DEFS[param].format(opts["uname"]))
        policy += "\n" + (
            MACRO_CALLS[arg][0].format(
                " ".join([opts["uname"] + s for s in MACRO_CALLS[arg][1]])
            )
        )
        # print("{}: {}".format(arg, value))

    policy = "\n".join(sorted(defs)) + policy

    with open("{}.cil".format(opts["uname"]), "w") as f:
        f.write(policy)

    print("Created {}.cil".format(opts["uname"]))
    print("Run the following commands to apply the new policy:")
    print("Install the new policy module")
    print(
        "# semodule -i {}.cil /usr/share/udica/macros/confined_user_macros.cil".format(
            opts["uname"]
        )
    )
    print("Create a default context file for the new user")
    print(
        "# sed -e ’s|user|{}|g’ /etc/selinux/targeted/contexts/users/user_u > /etc/selinux/targeted/contexts/users/{}_u".format(
            opts["uname"], opts["uname"]
        )
    )
    print("Map the new selinux user to an existing user account")
    print("# semanage login -a -s {}_u {}".format(opts["uname"], opts["uname"]))
    print("Fix labels in the user's home directory")
    print("# restorecon -RvF /home/{}".format(opts["uname"]))
