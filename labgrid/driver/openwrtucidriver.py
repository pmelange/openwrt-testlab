import attr
from time import sleep
from datetime import datetime

from labgrid.factory import target_factory
from labgrid.step import step
from labgrid.driver import Driver, ShellDriver

@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtUciDriver(Driver):
    """
    OpenWrtUciDriver is meant as a driver for OpenWrt's uci command
    line interface.

    So far the following actions are supported. add, add_list, del_list,
    set, delete.

    Args:
        config (dict, default={}): a list of uci operations with associated
        uci dict(s):

        config:
          - add:                   # add an unnamed section
              config: section-type # to add a named section, see set
          - add:
              config:
                - section-type1    # add multiple unnamed sections
                - section-type2
          - add_list:
              config:
                section1:
                  option1: value1
                  option1: value2
                section2:
                  option2: value3
          - add_list:
              config:
                section:
                  - option1: value1  # useful for when adding multiple    
                  - option1: value2  # list options of the same name 
                  - option1: value3
          - del_list:
              config:
                section:
                  option1: value1
                  option2: value2
          - del_list:
              config:
                section:
                  - option1: value1  # useful for when deleting multiple    
                  - option1: value2  # list options of the same name 
                  - option1: value3
          - set:
              config:
                section: sectionname # add a named section
          - set:
              config1:
                section1:
                  option1: value1
                  option2: value2
                section2:
                  option3: value3
                  option4: value4
              config2:
                section3:
                  option5: value5
          - delete:
              config: section      # delete a section
          - delete:
              config:
                section1: option   # delete an option
                section2: option
          - delete:
              config:
                section:
                  option: index    # delete a list option by index number
          - delete:
              config:
                section:
                  option:
                    - 2           # delete multiple list options by index
                    - 1           # warning, when deleteing idx 1, then
                                  # idx==2 will become idx 1.

    Example: - setting up a router to use a single port (wan) with VLAN
    tagging for br-lan Set a different IP on the lan interface and a hostname.

        OpenWrtUciDriver:
          config:
            - set:
                network:
                  lan:
                    ipaddr: '192.168.101.1'
                system:
                  "@system[0]":
                    hostname: 'testdev01'
            - add_list:
                network:
                  "@device[0]":     # br-lan
                    ports: 'wan.101'
    """
    bindings = { "shell": ShellDriver, }
    config = attr.ib(default=attr.Factory(list), validator=attr.validators.instance_of(list))
    auto_commit = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    auto_reload = attr.ib(default=True, validator=attr.validators.instance_of(bool))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass

    @Driver.check_active
    @step(args=['config', 'section_type'])
    def add(self, config: str, section_type: str):
        cmd = f"""uci add {config} {section_type}"""
        self.shell.run(cmd)

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'value'])
    def add_list(self, config: str, section: str, option: str, value: str):
        cmd = f"""uci add_list {config}.{section}.{option}="{value}" """
        self.shell.run(cmd)

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'value'])
    def del_list(self, config: str, section: str, option: str, value: str):
        cmd = f"""uci del_list {config}.{section}.{option}="{value}" """
        self.shell.run(cmd)
 
    @Driver.check_active
    @step(args=['config', 'section', 'option'])
    def get(self, config: str, section: str, option: str):
        return self.shell.run(f"""uci get {config}.{section}.{option}""")

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'value'])
    def set(self, config: str, section: str, option: str|None, value:str):
        if option is None:
            # create a new named section, therefore the strange order
            cmd = f"""uci set {config}.{value}={section}"""
        else:
            # set an option value
            cmd = f"""uci set {config}.{section}.{option}="{value}" """
        self.shell.run(cmd)

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'idx'])
    def delete(self, config: str, section: str, option: str|None, idx: int|None):
        if option is None:
            cmd = f"""uci delete {config}.{section}"""
        elif idx is None:
            cmd = f"""uci delete {config}.{section}.{option}"""
        else:
            cmd = f"""uci delete {config}.{section}.{option}={idx}"""
        self.shell.run(cmd)

    @Driver.check_active
    @step(args=['config'])
    def commit(self, config: str = None):
        if config is not None:
            cmd = f"""uci commit {config}"""
        else:
            cmd = f"""uci commit"""
        return self.shell.run(cmd)

    @Driver.check_active
    @step()
    def reload_config(self):
        cmd = f"""reload_config"""
        result = self.shell.run(cmd)
        sleep(2) # let the system reconfigure before going furthen
        self.shell.run("/etc/init.d/dnsmasq restart")
        return result

    def _find_bridge_device(self, device):
        if device.startswith('br-'):
            idx = 0
            result = [0, 0, 0]
            while result[2] == 0:
                result = self.get('network', 
                                  f"""@device[{idx}]""", 
                                  'name')
                if result[2] == 0 and result[0][0] == device:
                    return f"""@device[{idx}]"""
                idx += 1
            return None
        return None

    def _find_switch_vlan(self, vlan):
        idx = 0
        result = [0, 0, 0]
        while result[2] == 0:
            result = self.get('network',
                              f"""@switch_vlan[{idx}]""",
                              'vlan')
            if result[2] == 0 and result[0][0] == vlan:
                return f"""@switch_vlan[{idx}]"""
            idx += 1
        return None

    def _configure_options(self):
        # configure based on target's options
        # hostname
        oldhostname, _, _ = self.get('system', '@system[0]', 'hostname')
        result = self.target.env.config.get_target_option(self.target.name,
                                                          'hostname',
                                                          oldhostname[0])
        self.set('system', '@system[0]', 'hostname', result)
        # network
        lan_dev = self.get('network', 'lan', 'device')
        lan_device = lan_dev[0][0]
        wan_dev = self.get('network', 'wan', 'device')
        wan_device = wan_dev[0][0]

        lan_vlan = self.target.env.config.get_target_option(self.target.name,
                                                            'lan_vlan')
        lan_ip = self.target.env.config.get_target_option(self.target.name,
                                                          'lan_ip')
        lan_netmask = self.target.env.config.get_target_option(self.target.name,
                                                               'lan_netmask',
                                                               '255.255.255.0')
        # set LAN IP address
        self.set('network', 'lan', 'ipaddr', lan_ip)
        self.set('network', 'lan', 'netmask', lan_netmask)

        # assume DSA switch unless 'swconfig' is installed and lists something
        dsa = True
        _, _, errorcode = self.shell.run("which swconfig")
        if errorcode == 0:
            result, _, _ = self.shell.run("swconfig list")
            if "Found" in result[0]:
                dsa = False
        if dsa == True:
            # DSA switch
            connected_port = self.target.env.config.get_target_option(self.target.name,
                                                                      'connected_port')
            if lan_dev[2] == 0:
                lan_dev_section = self._find_bridge_device(lan_device)
                self.del_list('network', lan_dev_section, 'ports', connected_port)
                self.add_list('network', lan_dev_section, 'ports', 
                              connected_port + '.' + str(lan_vlan))
                if wan_dev[2] == 0:
                    wan_dev_section = self._find_bridge_device(wan_device)
                    if wan_dev_section is None:
                        if wan_device != connected_port:
                            self.add_list('network', lan_dev_section, 'ports', 
                                          wan_device)
                        self.set('network', 'wan', 'device', connected_port)
                        self.set('network', 'wan6', 'device', connected_port)
                    else:
                        # There is a WAN device section, remove all ports and
                        # add the connected_port
                        ports = self.get('network', wan_dev_section, 'ports')
                        if ports[2] == 0:
                            for port in ports[0][0].split():
                                if port != connected_port:
                                    # add to lan bridge device
                                    self.add_list('network', lan_dev_section, 'ports', port)
                                self.del_list('network' , wan_dev_section, 'ports', port)
                        self.add_list('network', wan_dev_section, 'ports', connected_port)
                else:
                    # create WAN
                    self.set('network', 'interface', None, 'wan')
                    self.set('network', 'wan', 'proto', 'dhcp')
                    self.set('network', 'wan', 'device', connected_port)
                    self.set('network', 'interface', None, 'wan6')
                    self.set('network', 'wan6', 'proto', 'dhcpv6')
                    self.set('network', 'wan6', 'device', connected_port)

            else:
                # TODO There is no LAN interface.  WTF
                pass
        else:
            # swconfig switch
            ports = self.target.env.config.get_target_option(self.target.name,
                                                             'switch_ports')
            cpuport = self.target.env.config.get_target_option(self.target.name,
                                                               'switch_cpuport')
            connected_port = self.target.env.config.get_target_option(self.target.name,
                                                                      "switch_connected_port")
            switch_device = self.get('network', '@switch[0]', 'name')[0][0]
            # LAN
            if lan_dev[2] == 0:
                lan_dev_section = self._find_bridge_device(lan_device)
                # update device section to new vlan
                lan_ports = self.get('network', lan_dev_section, 'ports')[0][0]
                eth = lan_ports.split('.')[0]
                if '.' in lan_ports:
                    old_vlan = lan_ports.split('.')[1]
                else: # case where vlans were not set up
                    old_vlan = '1'
                self.del_list('network', lan_dev_section, 'ports', lan_ports)
                self.add_list('network', lan_dev_section, 'ports', 
                              eth + '.' + str(lan_vlan))
                # update switch_vlan section to new vlan and port config
                switch_vlan_section = self._find_switch_vlan(old_vlan)
                self.set('network', switch_vlan_section, 'vlan', lan_vlan)
                self.set('network', switch_vlan_section, 'vid', lan_vlan)
                portlist = ""
                for port in ports.split(' '):
                    portlist += port
                    if port == str(cpuport) or port == str(connected_port):
                        portlist += 't'
                    portlist += ' '
                portlist = portlist[:-1]
                self.set('network', switch_vlan_section, 'ports', portlist)
            else:
                # TODO There is no LAN interface, WTF
                pass
            
            # WAN
            wan_vlan = str(int(old_vlan)+10) # use a number > 10 to be safe
            wan_port = eth + '.' + wan_vlan
            if wan_dev[2] == 0:
                # WAN exists
                wan_dev_section = self._find_bridge_device(wan_device)
                if wan_dev_section is not None:
                    result = self.get('network', wan_dev_section, 'ports')
                    if result[2] != 0:
                        # no port on the wan device, add it
                        self.add_list('network', wan_dev_section, 'ports', wan_port) 
                    else:
                        # port (and vlan) exists, use it
                        wan_port = result[0][0]
                        if '.' in wan_port:
                            wan_vlan = wan_port.split('.')[1]
                else:
                    if '.' in wan_device:
                        wan_vlan = wan_device.split('.')[1]
                switch_vlan_section = self._find_switch_vlan(wan_vlan)
                
            else:
                # create WAN since it doesn't exist
                self.set('network', 'interface', None, 'wan')
                self.set('network', 'wan', 'proto', 'dhcp')
                self.set('network', 'wan', 'device', wan_port)
                self.set('network', 'interface', None, 'wan6')
                self.set('network', 'wan6', 'proto', 'dhcpv6')
                self.set('network', 'wan6', 'device', wan_port)
                switch_vlan_section = None

            if switch_vlan_section is None:
                # create the switch_vlan section
                switch_vlan_section = 'wan_vlan'
                self.set('network', 'switch_vlan', None, switch_vlan_section)
                self.set('network', switch_vlan_section, 'device', switch_device)
                self.set('network', switch_vlan_section, 'vlan', wan_vlan)
                self.set('network', switch_vlan_section, 'vid', wan_vlan)
            
            self.set('network', switch_vlan_section, 'ports', 
                     f"""{cpuport}t {connected_port}""")

    @Driver.check_active
    @step()
    def configure(self):
        # configure based on the target's environment options
        self._configure_options()

        # configure based on the config attribute
        if not isinstance(self.config, list):
            raise ValueError("The config must be a list of dictionaries:{self.config}")
        for actions in self.config:
            for action, configs in actions.items():
                if not isinstance(configs, dict):
                    raise ValueError("The action {action} must have a dictionary: {configs}")
                match action:
                    case "add":
                        self.add_dict(configs)
                    case "add_list":
                        self.add_list_dict(configs)
                    case "del_list":
                        self.del_list_dict(configs)
                    case "set":
                        self.set_dict(configs)
                    case "delete":
                        self.delete_dict(configs)
                    case _:
                        raise ValueError("action {action} is not implemented")
        # add a config setting to mark that we have done something
        self.set("system",
                 "@system[0]",
                 "labgridconfig",
                 datetime.now().strftime("%Y-%m-%d@%H:%M:%S"))
        self.commit()
        self.reload_config()

    @Driver.check_active
    @step(args=['configs'])
    def add_dict(self, configs: dict):
        for config, sections in configs.items():
            if isinstance(sections, str):
                self.add(config, sections)
            elif isinstance(sections, list):
                for section in sections:
                    self.add(config, section)
            else:
                raise ValueError(f"""add: sections must be a list of dictionaries or a dictionary: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def add_list_dict(self, configs: dict):
        for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""add_list: sections must be a dictionary: {configs}""")
            for section, options in sections.items():
                if not isinstance(options, dict):
                    raise ValueError(f"""add_list: options must be a dictionary: {configs}""")
                for option, values in options.items():
                    if isinstance(values, str):
                        self.add_list(config, section, option, values)
                    elif isinstance(values, list):
                        for value in values:
                            self.add_list(config, section, option, value)
                    else:
                        raise ValueError(f"""add_list: values must be a string or list: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def del_list_dict(self, configs: dict):
         for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""del_list: sections must be a dictionary: {configs}""")
            for section, options in sections.items():
                if not isinstance(options, dict):
                    raise ValueError(f"""del_list: options must be a dictionary: {configs}""")
                for option, values in options.items():
                    if isinstance(values, str):
                        self.del_list(config, section, option, values)
                    elif isinstance(values, list):
                        for value in values:
                            self.del_list(config, section, option, value)
                    else:
                        raise ValueError(f"""del_list: values must be a string or list: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def set_dict(self, configs: dict):
         for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""set: sections must be dictionary: {configs}""")
            for section, options in sections.items():
                if isinstance(options, str):
                    # creating new named section, use options as value
                    value = options
                    self.set(config, section, None, value)
                elif isinstance(options, dict):
                    for option, value in options.items():
                        self.set(config, section, option, value)
                else:
                    raise ValueError(f"""set: options must be a string or a dictionary: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def delete_dict(self, configs: dict):
        for config, sections, in configs.items():
            if isinstance(sections, str):
                # delete an etire secton
                self.delete(config, sections, None, None)
            elif isinstance(sections, dict):
                for section, options in sections.items():
                    if isinstance(options, str):
                        # delete an option from a section
                        self.delete(config, section, options, None)
                    elif isinstance(options, dict):
                        for option, values in options.items():
                            if isinstance(values, int):
                                # delete a list option by index
                                self.delete(config, section, option, values)
                            elif isinstance(values, list):
                                for idx in values:
                                    if isinstance(idx, int):
                                        # delete a list option by index
                                        self.delete(config, section, option, idx)
                                    else:
                                        raise ValueError(f"""delete: index must be an integer: {configs}""")
                            else:
                                raise ValueError(f"""delete: index must be an integer or list of integers: {configs}""")
                    else:
                        raise ValueError(f"""delete: options must be a string or a dictionary: {configs}""")
            else:
                raise ValueError(f"""delete: sections must be a string or a dictionary: {configs}""")

