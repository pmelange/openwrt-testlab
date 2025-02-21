import attr

from labgrid.factory import target_factory
from labgrid.util import gen_marker
from labgrid.step import step
from labgrid.driver import Driver
from labgrid.protocol import ConsoleProtocol

@target_factory.reg_driver
@attr.s(eq=False)
class OpenwrtUciDriver(Driver):
    """
    OpenwrtUciDriver is meant as a driver for Openwrt's uci command
    line interface.

    So far the following actions are supported. set, add_list, del_list.

    Args:
        config (dict): in the following format:

        config:
          configfilename:          # network:
            sectionname:           #   wan:
              optionname: value    #     proto: static              # set
            sectionname:           #   "@device[0]":                # br-lan
              optionname: value    #     macaddr: 00:11:22:33:44:55 # set
          configfilenname:         # firewall:
            sectionname:           #   "@zone[1]":                  # wan zone
              - add:               #     - add:                     # add_list
                  network: foo     #         network: foo
              - delete:            #     - delete:                  # del_list
                  network: wan     #         network: wan
    """
    bindings = {
            "console": ConsoleProtocol,
    }
    config = attr.ib(attr.validators.instance_of(dict))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    def _uci_set(self, attrib, value):
        cmd = f"""uci set {attrib}={value}"""
        self.console.sendline(cmd)

    def _uci_addlist(self, attrib, value):
        cmd = f"""uci add_list {attrib}={value}"""
        self.console.sendline(cmd)

    def _uci_dellist(self, attrib, value):
        cmd = f"""uci del_list {attrib}={value}"""
        self.console.sendline(cmd)

    @Driver.check_active
    @step()
    def configure(self):
        for configfile, sections in self.config.items():
            if isinstance(sections, dict):
                for section, options in sections.items():
                    if isinstance(options, dict):
                        for option, value in options.items():
                            attrib = f"""{configfile}.{section}.{option}"""
                            if isinstance(value, str):
                                self._uci_set(attrib, value)
                            elif isinstance(value, list):
                                raise ValueError
                    elif isinstance(options, list):
                        for actions in options:
                            for action, listoptions in actions.items():
                                if not isinstance(listoptions, dict):
                                    raise ValueError
                                for option, value in listoptions.items():
                                    attrib = f"""{configfile}.{section}.{option}"""
                                    if action == "delete":
                                        self._uci_dellist(attrib, value)
                                    elif action == "add":
                                        self._uci_addlist(attrib, value)
                                    else:
                                        raise ValueError
                    else:
                        raise ValueError
            elif isinstance(sections, list):
                raise NotImplementedError
            else:
                raise ValueError
        self.console.sendline(f"""uci commit""")
        self.console.sendline(f"""reload_config""")


