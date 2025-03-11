import enum

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError

from time import sleep

class Status(enum.Enum):
    unknown = 0
    network = 1

@target_factory.reg_driver
@attr.s(eq=False)
class NettestStrategy(Strategy):
    """OpenWrtFlashBootStrategy - Strategy to boot from flash"""
    bindings = {
        "iface": "NetworkInterfaceDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == Status.network:
            self.target.activate(self.iface)
            netsettings = self.iface.get_settings()
            print(self.iface)
            print(netsettings)
            self.iface.configure({
                "connection": {
                    "type": "802-3-ethernet",
                    "interface-name": "eth0",
                    },
                "ipv4": {
                    "method": "auto",
                    "route-metric": 1000,
                    "ignore-auto-dns": True,
                    "ignore-auto-routes": True,
                    "never-default": True,
                    },
                "ipv6": {
                    "method": "link-local",
                    },
                "vlan": {
                    "parent": "eth0",
                    "id": 202,
                    },
                })
            print("XXXXXXXXXXXXXXXXXXXXX")
            print(self.iface.get_settings())
            print(self.iface.get_state())
            print(self.iface.get_active_settings())
            self.target.deactivate(self.iface)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        elif status == Status.network:
            self.target.activate(self.network)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
