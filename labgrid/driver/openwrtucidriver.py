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

    So far the following actions are supported. add, add_list, del_list,
    set, delete.

    Args:
        config (dict): in the following format:

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

    def _add(self, config: str, section_type: str):
        cmd = f"""uci add {config} {section_type}"""
        self.console.sendline(cmd)

    def _add_list(self, config: str, section: str, option: str, value: str):
        cmd = f"""uci add_list {config}.{section}.{option}={value}"""
        self.console.sendline(cmd)

    def _del_list(self, config: str, section: str, option: str, value: str):
        cmd = f"""uci del_list {config}.{section}.{option}={value}"""
        self.console.sendline(cmd)

    def _set(self, config: str, section: str, option: str|None, value:str):
        if option is None:
            # create a new names section, therefore the strange order
            cmd = f"""uci set {config}.{value}={section}"""
        else:
            # set an option value
            cmd = f"""uci set {config}.{section}.{option}={value}"""
        self.console.sendline(cmd)

    def _delete(self, config: str, section: str, option: str|None, idx: int|None):
        if option is None:
            cmd = f"""uci delete {config}.{section}"""
        elif idx is None:
            cmd = f"""uci delete {config}.{section}.{option}"""
        else:
            cmd = f"""uci delete {config}.{section}.{option}={idx}"""
        self.console.sendline(cmd)

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
                        self.add(configs)
                    case "add_list":
                        self.add_list(configs)
                    case "del_list":
                        self.del_list(configs)
                    case "set":
                        self.set(configs)
                    case "delete":
                        self.delete(configs)
                    case _:
                        raise ValueError("action {action} is not implemented")
        self.commit()
        self.reload_config()

    @Driver.check_active
    @step(args=['configs'])
    def add(self, configs: dict):
        for config, sections in configs.items():
            if isinstance(sections, str):
                self._add(config, sections)
            elif isinstance(sections, list):
                for section in sections:
                    self._add(config, section)
            else:
                raise ValueError(f"""add: sections must be a list of dictionaries or a dictionary: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def add_list(self, configs: dict):
        for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""add_list: sections must be a dictionary: {configs}""")
            for section, options in sections.items():
                if not isinstance(options, dict):
                    raise ValueError(f"""add_list: options must be a dictionary: {configs}""")
                for option, values in options.items():
                    if isinstance(values, str):
                        self._add_list(config, section, option, values)
                    elif isinstance(values, list):
                        for value in values:
                            self._add_list(config, section, option, value)
                    else:
                        raise ValueError(f"""add_list: values must be a string or list: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def del_list(self, configs: dict):
         for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""del_list: sections must be a dictionary: {configs}""")
            for section, options in sections.items():
                if not isinstance(options, dict):
                    raise ValueError(f"""del_list: options must be a dictionary: {configs}""")
                for option, values in options.items():
                    if isinstance(values, str):
                        self._del_list(config, section, option, values)
                    elif isinstance(values, list):
                        for value in values:
                            self._del_list(config, section, option, value)
                    else:
                        raise ValueError(f"""del_list: values must be a string or list: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def set(self, configs: dict):
         for config, sections in configs.items():
            if not isinstance(sections, dict):
                raise ValueError(f"""set: sections must be dictionary: {configs}""")
            for section, options in sections.items():
                if isinstance(options, str):
                    # creating new named section, use options as value
                    value = options
                    self._set(config, section, None, value)
                elif isinstance(options, dict):
                    for option, value in options.items():
                        self._set(config, section, option, value)
                else:
                    raise ValueError(f"""set: options must be a string or a dictionary: {configs}""")

    @Driver.check_active
    @step(args=['configs'])
    def delete(self, configs: dict):
        for config, sections, in configs.items():
            if isinstance(sections, str):
                # delete an etire secton
                self._delete(config, sections, None, None)
            elif isinstance(sections, dict):
                for section, options in sections.items():
                    if isinstance(options, str):
                        # delete an option from a section
                        self._delete(config, section, options, None)
                    elif isinstance(options, dict):
                        for option, values in options.items():
                            if isinstance(values, int):
                                # delete a list option by index
                                self._delete(config, section, option, values)
                            elif isinstance(values, list):
                                for idx in values:
                                    if isinstance(idx, int):
                                        # delete a list option by index
                                        self._delete(config, section, option, idx)
                                    else:
                                        raise ValueError(f"""delete: index must be an integer: {configs}""")
                            else:
                                raise ValueError(f"""delete: index must be an integer or list of integers: {configs}""")
                    else:
                        raise ValueError(f"""delete: options must be a string or a dictionary: {configs}""")
            else:
                raise ValueError(f"""delete: sections must be a string or a dictionary: {configs}""")

    @Driver.check_active
    @step(args=['config'])
    def commit(self, config: str = None):
        if config is not None:
            self.console.sendline(f"""uci commit {config}""")
        else:
            self.console.sendline(f"""uci commit""")

    @Driver.check_active
    @step()
    def reload_config(self):
        self.console.sendline(f"""reload_config""")


