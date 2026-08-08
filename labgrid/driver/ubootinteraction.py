import re
import attr
from pexpect import TIMEOUT
from time import sleep

from labgrid.factory import target_factory
from labgrid.util import gen_marker, Timeout
from labgrid.util.ssh import sshmanager
from labgrid.step import step
from labgrid.driver import Driver, TFTPProviderDriver

from labgrid.protocol import ConsoleProtocol, PowerProtocol, ButtonProtocol
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
        "provider": TFTPProviderDriver,
        "power": PowerProtocol,
        "reset": ButtonProtocol,
        }
    image = attr.ib(default="", validator=attr.validators.instance_of(str))
    sleep = attr.ib(default=0, validator=attr.validators.instance_of(int))
    commands = attr.ib(default=[], validator=attr.validators.instance_of(list))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._imagepath = None

    def _run(self, cmd: str, *, timeout: int = 120, codec: str = "utf-8", decodeerrors: str = "strict"):  # pylint: disable=line-too-long
        """
        If Uboot is in Command-Line mode: Run command cmd and return it's
        output.

        Arguments:
        cmd - Command to run
        """
        # TODO: use codec, decodeerrors

        prompt = self.target.get_driver("UBootDriver", activate=False).prompt
        marker = gen_marker()

        # Create multi-part command like we would do for a normal uboot.
        # but since this simple uboot does not have an echo-command we will
        # handle it's error message as an echo-output.
        # additionally we are not able to get the command's return code and
        # will always return 0.
        cmp_command = f"echo{marker}; {cmd}; echo{marker}"

        self.console.sendline(cmp_command)
        _, before, _, _ = self.console.expect(prompt, timeout=timeout)

        data = re_vt100.sub(
            '', before.decode('utf-8'), count=1000000
        ).replace("\r", "").split("\n")
        data = data[1:]
        data = data[data.index(f"Unknown command 'echo{marker}' - try 'help'") +1 :]
        data = data[:data.index(f"Unknown command 'echo{marker}' - try 'help'")]
        if len(data) >= 1:
            if data[0].startswith("Unknown command '"):
                return (data, [], 1)
        return (data, [], 0)

    @step()
    def prepare(self):
        # set up image for tftp server
        if self.image != "":
            self._imagepath = self.provider.stage(self.target.env.config.get_image_path(self.image))
        if self.sleep > 0:
            sleep(self.sleep)

    @step()
    def do_commands(self):
        for command in self.commands[:-1]:
            if self._imagepath is not None:
                command = re.sub(r"\$IMAGE", self._imagepath, command)
            self._run(command)
        if len(self.commands) > 0:
            command = re.sub(r"\$IMAGE", self._imagepath, self.commands[-1])
            self.console.sendline(command)

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
class UBootInteractionRamboot(UBootInteraction):
    mac = attr.ib(default="", validator=attr.validators.instance_of(str))
    bootpip = attr.ib(default="", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @step()
    def prepare(self):
        super().prepare() # set up tftp

        # set up bootp if a mac address and bootpip address are provided
        if self.mac != "" and self.bootpip != "":
            if re.match("^ENV", self.mac):
                result, _, _ = self._run("printenv " + self.mac[4:])
                self.mac = result[0].split("=", 1)[1]
            # set up dnsmasq on the exporter to set up bootp
            con = sshmanager.get(self.provider.provider.host)
            place = self.target.env.get_target().get_resource("RemotePlace").name
            filename = (place + "-dnsmasq.conf")
            config = ("dhcp-host=" + self.mac + "," + self.bootpip + ",set:" + place + 
                      "\ndhcp-option=tag:" + place + ",option:bootfile-name," + self._imagepath + "\n")
            fd = open(f"""/tmp/{filename}""", "w")
            fd.write(config)
            fd.close()
            con.put_file(f"""/tmp/{filename}""", "/tmp")
            con.run(f"""sudo mv /tmp/{filename} /etc/dnsmasq.d""")
            con.run(f"""grep -v {self.bootpip} /var/lib/misc/dnsmasq.leases > /tmp/dnsmasq.leases""")
            con.run("sudo mv /tmp/dnsmasq.leases /var/lib/misc")
            con.run("sudo systemctl restart dnsmasq.service")

@target_factory.reg_driver
@attr.s(eq=False)
class MikrotikUBootInteractionRamboot(UBootInteractionRamboot):
    mac = attr.ib(default="", validator=attr.validators.instance_of(str))
    bootpip = attr.ib(default="", validator=attr.validators.instance_of(str))
    cycle_power = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    hold_reset = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    hold_timeout = attr.ib(default=0, validator=attr.validators.instance_of(int))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @step()
    def prepare(self):
        super().prepare() # set up tftp and dnsmasq

        if self.mac != "" and self.bootpip != "":
            self.reset.press()
            self.power.cycle()
            sleep(self.hold_timeout)
            self.reset.release()

