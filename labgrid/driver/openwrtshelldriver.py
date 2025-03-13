# pylint: disable=unused-argument
"""The OpenWrtShellDriver implements the ShellDriver with OpenWrt specific
   setting and methods."""
import os
import io
import re
import shlex
import ipaddress
from datetime import datetime

import attr
from pexpect import TIMEOUT

from labgrid.factory import target_factory
from labgrid.protocol import ConsoleProtocol
from labgrid.step import step
from labgrid.util import Timeout
from labgrid.driver import Driver, ShellDriver
from labgrid.driver.exception import ExecutionError


@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtShellDriver(ShellDriver):
    """OpenWrtShellDriver - Driver to execute commands on the shell
    OpenWrtShellDriver inherits from ShellDriver and binds on top of a 
    ConsoleProtocol.  All Arguments are set to OpenWrt standard values,
    reducing the amount of options needed in the environment.yaml definition.

    On activation, the ShellDriver will look for the login prompt on the 
    console, wait until the init process is far enough along for the system
    to settle down, optionally put the ssh_key_file on the system, and to
    provide shell access.

    Args:
        prompt (regex): the shell prompt to detect, default set to OpenWrt 
            standard
        login_prompt (regex): the login prompt to detect, default set to 
            OpenWrt standard
        username (str): username to login with, default set to OpenWrt standard
        password (str): password to login with (not needed wit OpenWrt standard)
        keyfile (str): keyfile to bind mount over users authorized keys
        dest_authorized_keys (str): optional, 
            default="/etc/dropbear/authorized_keys", filename of the 
            authorized_keys file, set to OpenWrt standard
        login_timeout (int): optional, timeout for login prompt detection, 
            default set to OpenWrt standard
        console_ready (regex): optional, pattern used by the kernel to inform 
            the user that a console can be activated by pressing enter, 
            default set to OpenWrt standard
        await_login_timeout (int): optional, time in seconds of silence that 
            needs to pass before sending a newline to device, default set to 
            OpenWrt standard
        post_login_settle_time (int): optional, seconds of silence after 
            logging in before check for a prompt. Useful when the console 
            is interleaved with boot output which may interrupt prompt 
            detection, default set to OpenWrt standard
        ubus_ready: optional, default="session", the name of an ubus service to 
            become active the post_login_settle_time to determine if the 
            OpenWrt system is ready, default set to OpenWrt standard
        ubus_ready_timeout: optional, default="60", maximum amount of time to 
            wait for ubus to be ready, default set to OpenWrt standard
    """
    bindings = {"console": ConsoleProtocol, }
    prompt = attr.ib(default="root@[-\w()]+:[^ ]+ ", validator=attr.validators.instance_of(str))
    login_prompt = attr.ib(default="Please press Enter to activate this console.", validator=attr.validators.instance_of(str))
    username = attr.ib(default="root", validator=attr.validators.instance_of(str))
    password = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(str)))
    keyfile = attr.ib(default="", validator=attr.validators.instance_of(str))
    dest_authorized_keys = attr.ib(default="/etc/dropbear/authorized_keys", validator=attr.validators.instance_of(str))
    login_timeout = attr.ib(default=120, validator=attr.validators.instance_of(int))
    console_ready = attr.ib(default="", validator=attr.validators.instance_of(str))
    await_login_timeout = attr.ib(default=30, validator=attr.validators.instance_of(int))
    post_login_settle_time = attr.ib(default=5, validator=attr.validators.instance_of(int))
    ubus_ready = attr.ib(default="session", validator=attr.validators.instance_of(str))
    ubus_ready_timeout = attr.ib(default=60.0, validator=attr.validators.instance_of(float))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        # force the super().on_activate to not put the ssh key, we will do it
        keyfile = self.keyfile
        self.keyfile = ""

        status = self._status
        super().on_activate()

        if status == 0:
            self._wait_ubus()

        self.keyfile = keyfile
        if self.keyfile:
            keyfile_path = self.keyfile
            if self.target.env:
                keyfile_path = self.target.env.config.resolve_path(self.keyfile)
            self._put_ssh_key(keyfile_path, self.dest_authorized_keys)

    @step()
    def _wait_ubus(self):
        """ Waits until the ubus object wiat_ubus is available"""
        timeout = Timeout(self.ubus_ready_timeout)
        while not timeout.expired:
            _, _, exitcode = self._run(f"""ubus -t 10 wait_for {self.ubus_ready}""",
                                       timeout=timeout.remaining)
            if exitcode == 0:
                return
        if exitcode != 0:
            raise ExecutionError(f"""Ubus wait timeout({self.ubus_ready_timeout} sec) expired""")

    @Driver.check_active
    @step(args=['binfile', 'force', 'keepconfig'])
    def sysupgrade(self, binfile: str, force=False, keepconfig=True):
        cmd = " ".join(["sysupgrade",
                        "--force" if force else "",
                        "-n" if not keepconfig else "",
                        binfile])
        try:
            self._run(cmd, timeout=15.0)
        except TIMEOUT:
            pass

    @Driver.check_active
    @step()
    def backup(self):
        time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"""/tmp/backup-{time}.tar.gz"""
        cmd = f"""sysupgrade -b {filename}"""
        self._run(cmd)
        return filename

    @Driver.check_active
    @step(args=['filename'])
    def restore(self, filename):
        self._run(f"""sysupgrade -r {filename}""")

    @Driver.check_active
    @step()
    def get_dhcpd_leases(self):
        results, _, errorcode = self._run("cat /tmp/dhcp.leases")
        leases = []
        if errorcode != 0:
            for line in results:
                line = line.strip().split()
                if line[3] == "*":
                    line[3] = None
                if line[4] == "*":
                    line[4] = None
                leases.append(
                    {
                        "expire": int(line[0]),
                        "mac": line[1],
                        "ip": line[2],
                        "hostname": line[3],
                        "id": line[4],
                    }
                )
        return leases
