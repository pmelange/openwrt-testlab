import attr
from pexpect import TIMEOUT
from time import sleep

from labgrid.factory import target_factory
from labgrid.util import gen_marker, Timeout
from labgrid.step import step
from labgrid.driver import Driver

from labgrid.protocol import ConsoleProtocol
from labgrid.util import re_vt100

@attr.s(eq=False)
class UBootInteraction(Driver):
    """
    SmallUBootDriver is meant as a driver for UBoot with only little
    functionality compared to standard a standard UBoot.
    Especially is copes with the following limitations:

    - The UBoot does not have a real password-prompt but can be activated by
      entering a "secret" after a message was displayed.
    - The command line is does not have a build-in echo command. Thus this
      driver uses 'Unknown Command' messages as marker before and after the
      output of a command.
    - Since there is no echo we can not return the exit code of the command.
      Commands will always return 0 unless the command was not found.

    This driver needs the following features activated in UBoot to work:

    - The UBoot must not have real password prompt. Instead it must be
      keyword activated.
      For example it should be activated by a dialog like the following:
      UBoot: "Autobooting in 1s..."
      Labgrid: "secret"
      UBoot: <switching to console>
    - The UBoot must be able to parse multiple commands in a single
      line separated by ";".
    - The UBoot must support the "bootm" command to boot from a
      memory location.

    This driver was created especially for the following devices:

    - TP-Link WR841 v11

    Args:
        commands (list): a list of commands to boot from ROM
    """

    bindings = {
        "console": ConsoleProtocol,
        }
    commands = attr.ib(default=[], validator=attr.validators.instance_of(list))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @step()
    def prepare(self):
        pass

    @step()
    def get_commands(self):
        return self.commands

    @step()
    def finish(self):
        pass

@target_factory.reg_driver
@attr.s(eq=False)
class UBootInteractionBoot(UBootInteraction):
    def __attrs_post_init__(self):
        super().__attrs_post_init__()

@target_factory.reg_driver
@attr.s(eq=False)
class UBootInteractionFlash(UBootInteraction):
    def __attrs_post_init__(self):
        super().__attrs_post_init__()

@target_factory.reg_driver
@attr.s(eq=False)
class UBootInteractionTftpboot(UBootInteraction):
    def __attrs_post_init__(self):
        super().__attrs_post_init__()

@target_factory.reg_driver
@attr.s(eq=False)
class UBootInteractionBootp(UBootInteraction):
    def __attrs_post_init__(self):
        super().__attrs_post_init__()

