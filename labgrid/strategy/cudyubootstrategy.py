import enum

import attr
from time import sleep

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError


class Status(enum.Enum):
    unknown = 0
    off = 1
    uboot = 2
    shell = 3
    initialconfig = 4
    config = 5

@target_factory.reg_driver
@attr.s(eq=False)
class CudyUBootStrategy(Strategy):
    """CudyUbootStrategy - Strategy to switch to uboot or shell"""
    bindings = {
        "power": "PowerProtocol",
        'reset': "ButtonProtocol", # used by CodySmallUBootDriver
        "console": "ConsoleProtocol",
        "uboot": "UBootDriver",
        "shell": "ShellDriver",
        "config": "OpenWrtUciDriver",
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
        elif status == Status.uboot:
            self.transition(Status.off)
            self.target.activate(self.console)
            # cycle power
            self.power.cycle()
            # interrupt uboot
            self.target.activate(self.uboot)
        elif status == Status.shell:
            # transition to uboot
            self.transition(Status.uboot)
            self.uboot.boot("")
            self.uboot.await_boot()
            self.target.activate(self.shell)
            self.shell.run("uptime; uname -a")
        elif status == Status.config:
            self.transition(Status.shell)
            self.target.activate(self.config)
            self.config.configure()
            self.target.deactivate(self.config)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.power)
        elif status == Status.uboot:
            self.target.activate(self.uboot)
        elif status == Status.shell:
            self.target.activate(self.shell)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
