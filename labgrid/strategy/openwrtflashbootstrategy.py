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
    initialconfig = 4
    config = 5

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
            # wait for there to be a logfile to read
            _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
            while errorcode != 0:
                _, _, errorcode = self.shell.run("ubus -t 10 wait_for log")
            # wait until init is complete
            _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")
            while errorcode != 0:
                sleep(5)
                _, _, errorcode = self.shell.run("logread -l 100 | grep init\ complete")
        elif status == Status.config:
            print(self)
            self.transition(Status.shell)
            self.target.activate(self.config)
            self.config.configure()
            self.target.deactivate(self.config)
            self.target.activate(self.luci)
            self.luci.set_field("cbid.ffwizward.1.pw1", "abc123")
            self.luci.set_field("cbid.ffwizward.1.pw2", "abc123")
            self.luci.submit_form()
            self.luci.select_pulldown("widget.cbid.ffwizward.1.net", "Freifunk Berlin")
            self.luci.set_field("cbid.ffwizward.1.hostname", "testdev02")
            self.luci.set_field("cbid.ffwizward.1.nickname", "nickname")
            self.luci.set_field("cbid.ffwizward.1.realname", "realname")
            self.luci.set_field("cbid.ffwizward.1.mail", "email@address")
            self.luci.set_field("cbid.ffwizward.1.location", "my street address")
            self.luci.set_field("cbid.ffwizward.1.lat", "56.789")
            self.luci.set_field("cbid.ffwizward.1.lon", "12.345")
            self.luci.set_field("cbid.ffwizward.1.alt", "12")
            self.luci.submit_form()
            self.luci.click_link("sharedInternet")
            self.luci.set_field("cbid.ffuplink.1.usersBandwidthDown", "60")
            self.luci.set_field("cbid.ffuplink.1.usersBandwidthUp", "20")
            self.luci.submit_form()
            self.luci.set_checkbox("cbid.ffwizard.1.stats", True)
            self.luci.submit_form()
            self.luci.set_field("cbid.ffwizard.1.meship_radio0", "10.0.0.1", True)
            self.luci.select_radiobutton("cbid.ffwizard.1.mode_radio0", "80211s", True)
            self.luci.set_field("cbid.ffwizard.1.meship_radio1", "10.0.0.2", True)
            self.luci.select_radiobutton("cbid.ffwizard.1.mode_radio1", "80211s", True)
            self.luci.set_field("cbid.ffwizard.1.ssid", "testdev02.berlin.freifunk.net")
            self.luci.set_field("cbid.ffwizard.1.dhcpmesh", "192.168.102.0/24")
            self.luci.submit_form()
            self.target.deactivate(self.luci)
        else:
            raise StrategyError(f"no transition found from {self.status} to {status}")
        self.status = status

    def force(self, status):
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.off:
            self.target.activate(self.power)
        elif status == Status.on:
            self.target.activate(self.on)
        elif status == Status.shell:
            self.target.activate(self.shell)
        else:
            raise StrategyError("can not force state {}".format(status))
        self.status = status
