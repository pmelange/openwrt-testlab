import os
import enum

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError
from labgrid.util import Timeout
from labgrid.util.ssh import sshmanager
from labgrid.step import step

from time import sleep

class Status(enum.Enum):
    unknown = 0
    off = 1
    on = 2
    reboot = 3
    reset = 4
    hardreset = 5
    rebooting = 6
    bootrom = 7
    config = 8
    ffwizard = 9
    flash = 10
    upgrade = 11
    forceflash = 12
    backup = 13
    restore = 14

@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtFlashBootStrategy(Strategy):
    """OpenWrtFlashBootStrategy - Strategy to boot from flash"""
    bindings = {
        "power": "PowerProtocol",
        'reset': "ButtonProtocol",
        "console": "ConsoleProtocol",
        "shell": "OpenWrtShellDriver",
        "config": "OpenWrtUciDriver",
        "ffwizard": "FreifunkWizardDriver",
        "ssh": "SSHDriver",
        "net": "NetworkInterfaceDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._shellready = False
        self.exporter_release_lease()

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

        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")

        elif status == self.status:
            return # nothing to do

        elif status == Status.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
            self._shellready = False
            self.exporter_release_lease()

        elif status == Status.on:
            self.transition(Status.off)
            self.target.activate(self.console)
            # cycle power
            self.power.cycle()

        elif status == Status.reboot:
            # runs reboot on the command if the shell is ready
            if self._shellready is True:
                self.shell.run("reboot")
            self._shellready = False
            self.transition(Status.bootrom)

        elif status == Status.reset:
            # runs firstboot
            self.transition(Status.bootrom)
            self.shell.run("firstboot -y")
            self.transition(Status.reboot)

        elif status == Status.hardreset:
            # use the reset button to reset the device
            self.transition(Status.bootrom)
            self.target.activate(self.reset)
            self.reset.press_for()
            self.transition(Status.rebooting)

        elif status == Status.rebooting:
            self.target.deactivate(self.shell)
            self._shellready = False
            self.transition(Status.bootrom)

        elif status == Status.bootrom:
            # monitor the serial console until it can be accessed
            self.target.activate(self.power)
            if self.power.get() is not True:
                self.transition(Status.on)
            if self._shellready is not True:
                self.target.activate(self.shell)
            self._shellready = True

        elif status == Status.config:
            # Preconfigure a fresh router based on the env's config params
            # This can set up the WAN/LAN ports as needed as well as
            # predefined IP addresses.
            self.transition(Status.bootrom)
            self.target.activate(self.config)
            self.config.configure()
            self.target.deactivate(self.config)

        elif status == Status.ffwizard:
            # Run the ffwizard once the firstconfig is set up
            self.transition(Status.config)
            self.exporter_renew_lease()
            self.target.activate(self.ffwizard)
            self.ffwizard.configure()
            self.target.deactivate(self.ffwizard)
            # ffwizard is complete, wait until reboot is finished.
            self.transition(Status.rebooting)
            # Ensure the iface on the exporter is set up right
            self.exporter_renew_lease()
            # We are running

        elif status == Status.flash:
            # flash a new image without keeping the settings
            self.exporter_renew_lease()
            image = self.target.env.config.get_image_path("firmware")
            self.target.activate(self.ssh)
            self.ssh.put(image, "/tmp/image.bin")
            self.shell.sysupgrade("/tmp/image.bin", keepconfig=False)
            self.transition(Status.rebooting)

        elif status == Status.upgrade:
            # flash new new image with keeping the settings
            self.exporter_renew_lease()
            image = self.target.env.config.get_image_path("firmware")
            self.target.activate(self.ssh)
            self.ssh.put(image, "/tmp/image.bin")
            self.shell.sysupgrade("/tmp/image.bin")
            self.transition(Status.rebooting)

        elif status == Status.forceflash:
            # force flash without keeping the settings
            self.exporter_renew_lease()
            image = self.target.env.config.get_image_path("firmware")
            self.target.activate(self.ssh)
            self.ssh.put(image, "/tmp/image.bin")
            self.shell.sysupgrade("/tmp/image.bin", force=True, keepconfig=False)
            self.transition(Status.rebooting)

        elif status == Status.backup:
            self.exporter_renew_lease()
            filename = self.shell.backup()
            self.target.activate(self.ssh)
            path = self.target.env.config.get_path("backup")
            self.ssh.get(filename, path)

        elif status == Status.restore:
            self.exporter_renew_lease()
            backup = self.target.env.config.get_image_path("backup")
            self.target.activate(self.ssh)
            self.ssh.put(backup, "/tmp")
            self.shell.restore(f"""/tmp/{os.path.basename(backup)}""")
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        
        self.status = status

    @step(args=['status'])
    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.transition(Status.off)
        elif status == Status.on:
            self.target.activate(self.shell)
            self._shellready = True
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
