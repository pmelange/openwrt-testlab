import attr
import re
from pexpect import TIMEOUT

from labgrid.factory import target_factory
from labgrid.util import gen_marker, Timeout
from labgrid.step import step
from labgrid.driver import Driver

from labgrid.protocol import ConsoleProtocol
from labgrid.driver import UBootDriver
from labgrid.util import re_vt100
from driver.ubootinteraction import UBootInteractionBoot, UBootInteractionFlash, UBootInteractionTftpboot, UBootInteractionBootp

@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtRouterBootDriver(UBootDriver):
    """
    OpenWrtUBootDriver is meant as a driver for UBoot with only little
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
        boot_secret (str): optional, secret used to unlock prompt
        boot_secret_nolf (bool): optional, send boot_secret without new line
        login_timeout (int): optional, timeout for login prompt detection,
    """
    bindings = {
            "console": ConsoleProtocol,
            "_boot": {UBootInteractionBoot, None},
            "_flash": {UBootInteractionFlash, None},
            "_tftpboot": {UBootInteractionTftpboot, None},
            "_bootp": {UBootInteractionBootp, None},
            }

    boot_expression = attr.ib(default=r"U-Boot 20\d+", validator=attr.validators.instance_of(str))
    boot_secret = attr.ib(default="a", validator=attr.validators.instance_of(str))
    boot_secret_nolf = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    login_timeout = attr.ib(default=60, validator=attr.validators.instance_of(int))

    @step()
    def _await_prompt(self):
        """
        Await autoboot_expression. If this line was read enter the 'secret' (or a
        single character) to interrupt normal boot.
        """

        # wait for boot expression. Afterwards enter secret
        timeout = Timeout(float(self.login_timeout))
        expectations = [self.prompt,
                        self.boot_expression,
                        TIMEOUT]
        last_before = None

        while True:
            index, before, _, _ =  self.console.expect(expectations, timeout=2)

            if index == 0:
                # we have the uboot prompt
                self._status = 1
                break

            elif index == 1:
                # interrupt autoboot
                secret = self.boot_secret.encode('ASCII')
                if self.boot_secret.startswith('\\x'):
                    try:
                        secret = bytearray.fromhex(self.boot_secret[2:])
                    except ValueError:
                        pass

                if self.boot_secret_nolf:
                    self.console.write(secret)
                else:
                    self.console.sendline(self.boot_secret)

                continue

            elif index == 2:
                if before == last_before:
                    self.console.sendline("")
                if timeout.expired:
                    raise TIMEOUT(
                            f"""Timeout of {self.login_timeout} seconds exceeded during waiting for login"""
                            )
            last_before = before

            try:
                self._check_prompt()
            except TIMEOUT:
                pass

        for command in self.init_commands:
            self._run(command)

    def _run(self, cmd: str, *, timeout: int = 30, codec: str = "utf-8", decodeerrors: str = "strict"):  # pylint: disable=line-too-long
        """
        If Uboot is in Command-Line mode: Run command cmd and return it's
        output.

        Arguments:
        cmd - Command to run
        """
        # TODO: use codec, decodeerrors

        # Check if Uboot is in command line mode
        if self._status != 1:
            return None

        marker = gen_marker()

        # Create multi-part command like we would do for a normal uboot.
        # but since this simple uboot does not have an echo-command we will
        # handle it's error message as an echo-output.
        # additionally we are not able to get the command's return code and
        # will always return 0.
        cmp_command = f"echo{marker}; {cmd}; echo{marker}"

        self.console.sendline(cmp_command)
        _, before, _, _ = self.console.expect(self.prompt, timeout=timeout)

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

    @step(args=["driver"])
    def _do_interaction(self, driver):
        self.target.activate(driver)
        driver.prepare()
        driver.do_commands()
        driver.finish()
        self.target.deactivate(driver)

    @Driver.check_active
    @step()
    def boot(self):
        if self._boot is not None:
            self._do_interaction(self._boot)
        # TODO Add exception if None

    @Driver.check_active
    @step()
    def flash(self):
        if self._flash is not None:
            self._do_interaction(self._flash)

    @Driver.check_active
    @step()
    def tftpboot(self):
        if self._tftpboot is not None:
            self._do_interaction(self._tftpboot)

    @Driver.check_active
    @step()
    def bootp(self):
        if self._bootp is not None:
            self._do_interaction(self._bootp)
