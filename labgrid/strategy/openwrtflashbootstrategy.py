import enum

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError

from time import sleep

class Status(enum.Enum):
    unknown = 0
    off = 1
    on = 2
    shell = 3
    wait_init = 4
    config = 5
    ffwizard = 6
    putfile = 7

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
        "luci": "OpenwrtLuCIDriver",
        "ffwizard": "FreifunkWizardDriver",
        "ssh": "SSHDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

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
        elif status == Status.on:
            self.transition(Status.off)
            self.target.activate(self.console)
            # cycle power
            self.power.cycle()
        elif status == Status.shell:
            # transition to on
            self.transition(Status.on)
            self.target.activate(self.shell)
            self.shell.run("uptime; uname -a")
        elif status == Status.wait_init:
            self.transition(Status.shell)
            # wait for there to be a logfile to read
            _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
            while errorcode != 0:
                _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
            # wait until init is complete
            _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")
            while errorcode != 0:
                sleep(5)
                _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")
            #self.shell.put("/home/pi/.ssh/id_rsa.pub", "/etc/dropbear")
            self.shell.run("cp ~/.ssh/authorized_keys /etc/dropbear")
        elif status == Status.config:
            self.transition(Status.wait_init)
            self.target.activate(self.config)
            self.config.configure()
            self.target.deactivate(self.config)
        elif status == Status.ffwizard:
            self.transition(Status.config)
            self.target.activate(self.ffwizard)
            self.ffwizard.configure()
            self.target.deactivate(self.ffwizard)
            self.target.deactivate(self.shell)
            self.target.activate(self.shell)
        elif status == Status.putfile:
            self.transition(Status.config)
            self.target.activate(self.ssh)
            self.ssh.put("/srv/tftp/uImage","/tmp")
            self.target.deactivate(self.ssh)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.off)
        elif status == Status.on:
            self.target.activate(self.on)
        elif status == Status.shell:
            self.target.activate(self.shell)
        elif status == Status.wait_init:
            self.target.activate(self.wait_init)
        elif status == Status.config:
            self.target.activate(self.config)
        elif status == Status.ffwizard:
            self.target.activate(self.ffwizard)
        elif status == Status.putfile:
            self.target.activate(self.putfile)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
