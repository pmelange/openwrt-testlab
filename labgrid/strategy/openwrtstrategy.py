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
    boot = auto()
    ramboot = auto()
    flash = auto()
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
        "tftp": "TFTPProviderDriver",
        "uci": "OpenWrtUciDriver",
        "ssh": "SSHDriver",
        "net": "NetworkInterfaceDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.exporter_release_lease()
        self._features = self.target.env.get_target_features()

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
                self.exporter_release_lease()
                self.target.deachtivate(self.power)

            case Status.on:
                self.transition(Status.off)
                self.target.activate(self.console)
                self.power.cycle()
                self.target.deactivate(self.power)

            case status.boot:
                self.target.activate(self.uboot)
                self.uboot.boot()
                self.target.deactivate(self.uboot)

            case status.ramboot:
                # boot an initramfs image if supported
                if 'uboot_ramboot' in self._features:
                    self.target.activate(self.uboot)
                    self.uboot.ramboot()
                    self.target.deactivate(self.uboot)
                else:
                    raise StrategyError("The env.yaml file does not support a ramboot method")

            case status.flash:
                # determine how to flash the target based on the 'features'
                if 'ramboot_then_flash' in self._features:
                    self.target.activate(self.uboot)
                    self.uboot.image = self.target.env.config.get_image_path("rescue_ramboot")
                    self.uboot.ramboot()
                    self.target.deactivate(self.uboot)
                    self.transition(Status.config)
                    self.target.activate(self.ssh)
                    self.ssh.put(self.target.env.config.get_image_path("target"),
                                 "/tmp/image.bin")
                    self.target.deactivate(self.ssh)
                    # flash the target image, reboots automatically
                    self.shell.sysupgrade("/tmp/image.bin", force=True, keepconfig=False)
                    self.target.deactivate(self.shell)
                    self.target.activate(self.shell)
                elif 'uboot_flash' in self._features:
                    self.target.activate(self.uboot)
                    self.uboot.flash()
                    self.target.deactivate(self.uboot)
                else:
                    raise StrategyError("The env.yaml file does not support a flash method")

            case Status.shell:
                self.target.activate(self.power)
                if self.power.get() == False:
                    self.transition(Status.on)
                self.target.deactivate(self.power)
                self.target.activate(self.shell)

            case Status.config:
                # Preconfigure a fresh router based on the env's config params
                # This can set up the WAN/LAN ports as needed as well as
                # predefined IP addresses.
                self.transition(Status.shell)
                self.target.activate(self.uci)
                _, _, error = self.uci.get("system", 
                                           "@system[0]", 
                                           "labgridconfig")
                if error != 0:
                    self.uci.configure()
                self.target.deactivate(self.uci)
                self.exporter_renew_lease()

            case Status.reboot:
                # runs reboot on the command if the shell is ready
                self.transition(Status.shell)
                self.target.activate(self.shell)
                self.shell.run("reboot")
                self.exporter_release_lease()
                self.target.deactivate(self.shell)
                self.target.activate(self.shell)

            case Status.reset:
                # runs firstboot
                self.transition(Status.shell)
                self.shell.run("firstboot -y")
                self.transition(Status.reboot)

            case Status.hardreset:
                # use the reset button to reset the device
                self.transition(Status.shell)
                self.target.activate(self.reset)
                self.reset.press_for()
                self.target.deactivate(self.reset)
                # Hard reset done, reboots automatically
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
