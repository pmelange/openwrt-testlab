import attr

from labgrid.factory import target_factory
from labgrid.util import gen_marker
from labgrid.step import step
from labgrid.driver import Driver

from driver.openwrtlucidriver import OpenwrtLuCIDriver

@target_factory.reg_driver
@attr.s(eq=False)
class FreifunkWizardDriver(Driver):
    bindings = {
            "luci": "OpenwrtLuCIDriver",
            }
    """
    Driver for the Freifunk wizard
    - This driver assumes that the router is freshly installed with no
    configuration.  Using this on a router with a password or where the
    wizard does not automatically start will cause problems
    """

    # Manditory attributes
    address = attr.ib(validator=attr.validators.instance_of(str))
    password = attr.ib(validator=attr.validators.instance_of(str))
    hostname = attr.ib(validator=attr.validators.instance_of(str))
    nickname = attr.ib(validator=attr.validators.instance_of(str))
    realname = attr.ib(validator=attr.validators.instance_of(str))
    email = attr.ib(validator=attr.validators.instance_of(str))
    location = attr.ib(validator=attr.validators.instance_of(str))
    lat = attr.ib(validator=attr.validators.instance_of(str))
    lon = attr.ib(validator=attr.validators.instance_of(str))
    bw_down = attr.ib(validator=attr.validators.instance_of(str))
    bw_up = attr.ib(validator=attr.validators.instance_of(str))
    meship_radio0 = attr.ib(validator=attr.validators.instance_of(str))
    meshmode_radio0 = attr.ib(validator=attr.validators.instance_of(str))
    meship_radio1 = attr.ib(validator=attr.validators.instance_of(str))
    meshmode_radio1 = attr.ib(validator=attr.validators.instance_of(str))
    dhcp = attr.ib(validator=attr.validators.instance_of(str))

    # default attributes
    network = attr.ib(default="Freifunk Berlin", validator=attr.validators.instance_of(str))
    alt = attr.ib(default="", validator=attr.validators.instance_of(str))
    sharedInternet = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    stats = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    ssid = attr.ib(default="berlin.freifunk.net", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    @Driver.check_active
    @step()
    def configure(self):
        self._url = f"""https://{self.address}/"""

        # start up the wizard
        self.luci.get(self._url)

        # Page 1, set the password
        self.luci.set_field("cbid.ffwizward.1.pw1", self.password)
        self.luci.set_field("cbid.ffwizward.1.pw2", self.password)
        self.luci.submit_form()

        # Page 2, general info
        self.luci.select_pulldown("widget.cbid.ffwizward.1.net", self.network)
        self.luci.set_field("cbid.ffwizward.1.hostname", self.hostname)
        self.luci.set_field("cbid.ffwizward.1.nickname", self.nickname)
        self.luci.set_field("cbid.ffwizward.1.realname", self.realname)
        self.luci.set_field("cbid.ffwizward.1.mail", self.email)
        self.luci.set_field("cbid.ffwizward.1.location", self.location)
        self.luci.set_field("cbid.ffwizward.1.lat", self.lat)
        self.luci.set_field("cbid.ffwizward.1.lon", self.lon)
        self.luci.set_field("cbid.ffwizward.1.alt", self.alt)
        self.luci.submit_form()

        # page 3, decide
        if not self.sharedInternet:
            self.luci.click_link("optionalConfigs")
        else:
            self.luci.click_link("sharedInternet")

            # page 3.5, shared internet
            self.luci.set_field("cbid.ffuplink.1.usersBandwidthDown", self.bw_down)
            self.luci.set_field("cbid.ffuplink.1.usersBandwidthUp", self.bw_up)
            self.luci.submit_form()

        # page 4, optional configs
        self.luci.set_checkbox("cbid.ffwizard.1.stats", self.stats)
        self.luci.submit_form()

        # page 5, wireless
        self.luci.set_field("cbid.ffwizard.1.meship_radio0", self.meship_radio0, True)
        self.luci.select_radiobutton("cbid.ffwizard.1.mode_radio0", self.meshmode_radio0, True)
        self.luci.set_field("cbid.ffwizard.1.meship_radio1", self.meship_radio1, True)
        self.luci.select_radiobutton("cbid.ffwizard.1.mode_radio1", self.meshmode_radio1, True)
        self.luci.set_field("cbid.ffwizard.1.ssid", self.ssid)
        self.luci.set_field("cbid.ffwizard.1.dhcpmesh", self.dhcp)
        self.luci.submit_form()

