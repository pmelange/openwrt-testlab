import attr
from time import sleep

from labgrid.factory import target_factory
from labgrid.util import gen_marker
from labgrid.step import step
from labgrid.driver import Driver, ShellDriver
from labgrid.protocol import ConsoleProtocol

@target_factory.reg_driver
@attr.s(eq=False)
class OpenwrtUciDriver(Driver):
    """
    OpenwrtUciDriver is meant as a driver for Openwrt's uci command
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

        OpenwrtUciDriver:
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
        cmd = f"""uci add_list {config}.{section}.{option}={value}"""
        self.shell.run(cmd)

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'value'])
    def del_list(self, config: str, section: str, option: str, value: str):
        cmd = f"""uci del_list {config}.{section}.{option}={value}"""
        self.shell.run(cmd)
 
    @Driver.check_active
    @step(args=['config', 'section', 'option'])
    def get(self, config: str, section: str, option: str):
        return self.shell.run(f"""uci get {config}.{section}.{option}""")

    @Driver.check_active
    @step(args=['config', 'section', 'option', 'value'])
    def set(self, config: str, section: str, option: str|None, value:str):
        if option is None:
            # create a new names section, therefore the strange order
            cmd = f"""uci set {config}.{value}={section}"""
        else:
            # set an option value
            cmd = f"""uci set {config}.{section}.{option}={value}"""
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
        data, _, errorcode = self.shell.run(cmd)
        sleep(0.5) # let the system reconfigure before going furthen
        return (data, [], errorcode)

    @Driver.check_active
    @step()
    def configure(self):
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

