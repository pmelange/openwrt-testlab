import os
import enum
from enum import auto
from pexpect import TIMEOUT

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError
from labgrid.util import Timeout
from labgrid.util.ssh import sshmanager
from labgrid.step import step

from time import sleep

class Status(enum.Enum):
    unknown = auto()
    off = auto()
    on = auto()
    uboot_shell = auto()
    uboot_boot = auto()
    uboot_flash = auto()
    uboot_tftpboot = auto()
    uboot_bootp = auto()
    shell = auto()
    config = auto()
    reboot = auto()
    reset = auto()
    hardreset = auto()

@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtStrategy(Strategy):
    """OpenWrtStrategy - Strategy to boot from flash"""
    bindings = {
        "power": "PowerProtocol",
        'reset': "ButtonProtocol",
        "console": "ConsoleProtocol",
        "uboot": "LinuxBootProtocol",
        "shell": "OpenWrtShellDriver",
        "uci": "OpenWrtUciDriver",
        "ssh": "SSHDriver",
        "net": "NetworkInterfaceDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._ubootready = False
        self._shellready = False
        self._configured = None
        self.exporter_release_lease()

    @step()         
    def determine_status(self):
        # try to determine the current status
        self.target.activate(self.power)
        if self.power.get():
            self.status = Status.on
            self.target.activate(self.console)
            expectations = [self.uboot.prompt,
                            self.shell.prompt,
                            TIMEOUT]
            self.console.sendline("")
            index, _, _, _ = self.console.expect(expectations, timeout=5)
            if index == 0:
                self._ubootready = True
                self.status = Status.uboot_shell
            elif index == 1:
                self._shellready = True
                self.status = Status.shell
            else:
                # unable to determine state.  Set to a know state of off.
                self.power.off()
                self._shellready = False
                # raise StrategyError("Unable to determine state")
            if self._shellready:
                # check to see if we are configured
                self.console.sendline("")
                self.target.activate(self.uci)
                _, _, error = self.uci.get("system", 
                                           "@system[0]", 
                                           "labgridconfig")
                if error == 0:
                    self.status = Status.config
                    self._configured = True
                    # We are at least configured, set up the networking
                    self.exporter_renew_lease()
                else:
                    self._configured = False

                self.target.deactivate(self.uci)
            #self.target.deactivate(self.console)
        if not self.power.get():
            # power is off
            self.status = Status.off
            self._shellready = False
            self._ubootready = False
            self._configured = None
            self.exporter_release_lease()
        print("Determined that the current state is:")
        print(f"""   status = {self.status.name}""")
        print(f"""   shellready = {self._shellready}""")
        print(f"""   ubootready = {self._ubootready}""")
        print(f"""   configured = {self._configured}""")

    @step()
    def exporter_release_lease(self):
        self.target.activate(self.net)
        con = sshmanager.get(self.net.iface.host)
        con.run(f"""sudo dhclient -r {self.net.iface.ifname}""")

    @step()
    def exporter_renew_lease(self):
        self.target.activate(self.net)
        con = sshmanager.get(self.net.iface.host)
        con.run(f"""sudo dhclient -r {self.net.iface.ifname}""")
        con.run(f"""sudo dhclient {self.net.iface.ifname}""")
        timeout = Timeout(60.0)
        while not timeout.expired:
            result, _, _ = con.run(f"""ip -f inet add show {self.net.iface.ifname}""")
            if len(result) > 0:
                return
            sleep(1)

        # Timeout encountered
        raise SystemError(f"""Unable to aquire lease on {self.net.iface.host} for interface {self.net.iface.ifname}""")

    @step(args=['status'])
    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]

        if self.status == Status.unknown:
            self.determine_status()
            
        #
        # State Machine starts here
        #
        match status:
            case Status.unknown:
                raise StrategyError(f"can not transition to {status}")

            case self.status:
                return # nothing to do

            case Status.off:
                self.target.deactivate(self.console)
                self.target.activate(self.power)
                self.power.off()
                self._shellready = False
                self._ubootready = False
                self.exporter_release_lease()

            case Status.on:
                self.transition(Status.off)
                self.target.activate(self.console)
                self.power.cycle()

            case Status.uboot_shell | Status.uboot_boot | Status.uboot_flash | Status.uboot_tftpboot | Status.uboot_bootp:

                self.target.activate(self.uboot)

                self._ubootready = True
                self._shellready = False
                self._configured = None
                match status:
                    case Status.uboot_boot:
                        self.uboot.boot()
                    case Status.uboot_flash:
                        self.uboot.flash()
                    case Status.uboot_tftpboot:
                        self.uboot.tftpboot()
                    case Status.uboot_bootp:
                        self.uboot.bootp()
                if status != Status.uboot_shell:
                    self._ubootready = False

            case Status.shell:
                if not self.power.get() or self._ubootready:
                    # reboot without uboot interaction
                    self.transition(Status.on)
                    self._shellready = False
                if not self._shellready:
                    self.target.activate(self.shell)
                    self._shellready = True
                if self._configured == None:
                    self.determine_status()

            case Status.config:
                # Preconfigure a fresh router based on the env's config params
                # This can set up the WAN/LAN ports as needed as well as
                # predefined IP addresses.
                if not self.power.get() or not self._shellready:
                    self.transition(Status.shell)
                if not self._configured:
                    self.target.activate(self.uci)
                    self.uci.configure()
                    self.target.deactivate(self.uci)
                    self._configured = True
                self.exporter_renew_lease()

            case Status.reboot:
                # runs reboot on the command if the shell is ready
                if not self._shellready:
                    self.transition(Status.shell)
                else:
                    self.target.activate(self.shell)
                    self.shell.run("reboot")
                    self._shellready = False
                    self.exporter_release_lease()
                    self.target.deactivate(self.shell)
                    self.target.activate(self.shell)

            case Status.reset:
                # runs firstboot
                if not self._shellready:
                    self.transition(Status.shell)
                else:
                    self.target.activate(self.shell)
                self.shell.run("firstboot -y")
                self._configured = None
                self.transition(Status.reboot)

            case Status.hardreset:
                # use the reset button to reset the device
                if not self._shellready:
                    self.transition(Status.shell)
                self.target.activate(self.reset)
                self.reset.press_for()
                self.target.deactivate(self.reset)
                # Hard reset done, reboots automatically
                self._shellready = False
                self._configured = None
                self.target.deactivate(self.shell)
                self.target.activate(self.shell)

            case _:
                raise StrategyError(f"""no transition found from {self.status} to {status}""")
        
        self.status = status

    @step(args=['status'])
    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        self.transition(status)
