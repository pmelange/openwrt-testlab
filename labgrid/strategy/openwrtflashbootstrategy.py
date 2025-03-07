import enum

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError
from labgrid.util.ssh import sshmanager

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

@target_factory.reg_driver
@attr.s(eq=False)
class OpenwrtFlashBootStrategy(Strategy):
    """OpenwrtFlashBootStrategy - Strategy to boot from flash"""
    bindings = {
        "power": "PowerProtocol",
        'reset': "ButtonProtocol",
        "console": "ConsoleProtocol",
        "shell": "ShellDriver",
        "config": "OpenwrtUciDriver",
        "ffwizard": "FreifunkWizardDriver",
        "ssh": "SSHDriver",
        "net": "NetworkInterfaceDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._shellready = False
        self.exporter_iface("down")

    def exporter_iface(self, state):
        self.target.activate(self.net)
        sshmanager.get(self.net.iface.host).run(f"""sudo if{state} {self.net.iface.ifname}""")

    def sysupgrade(self, opts = ""):
        # flash a new image with keeping the settings
        self.transition(Status.bootrom)
        self.exporter_iface("up")
        # transfer the image to the device
        image = self.target.env.config.get_image_path("firmware")
        self.target.activate(self.ssh)
        self.ssh.put(image, "/tmp/image.bin")
 
        # the try/except block is needed because the router will
        # reboot before the run command can return anything
        try:
            self.shell.run(f"""sysupgrade {opts} /tmp/image.bin""")
        except:
            pass

    def wait_init(self):
        """
        Wait for the boot process to finish.  First we need that 'log' is i
        available then we check the log until 'init complete' is announced
        """
        _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
        while errorcode != 0:
            _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
        # wait until init is complete
        _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")
        while errorcode != 0:
            sleep(5)
            _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")

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
            self._shellread = False
            self.exporter_iface("down")

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
            self.exporter_iface("down")
            self.transition(Status.bootrom)
            #self.exporter_iface("up")

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
                self.wait_init()
            self._shellready = True
            self.shell.run("cp ~/.ssh/authorized_keys /etc/dropbear")

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
            self.exporter_iface("up")
            self.target.activate(self.ffwizard)
            self.ffwizard.configure()
            self.target.deactivate(self.ffwizard)
            # ffwizard is complete, wait until reboot is finished.
            self.transition(Status.rebooting)
            # Ensure the iface on the exporter is set up right
            self.exporter_iface("down")
            self.exporter_iface("up")
            # We are running

        elif status == Status.flash:
            # flash a new image without keeping the settings
            self.sysupgrade("-n")
            self.transition(Status.rebooting)

        elif status == Status.upgrade:
            # flash new new image with keeping the settings
            self.sysupgrade()
            self.transition(Status.rebooting)

        elif status == Status.forceflash:
            # force flash without keeping the settings
            self.sysupgrade("--force -n")
            self.transition(Status.rebooting)

        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        
        self.status = status

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
