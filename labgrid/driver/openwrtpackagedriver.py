import attr
from enum import Enum, auto
from time import sleep
from datetime import datetime

from labgrid.factory import target_factory
from labgrid.step import step
from labgrid.driver import Driver, ShellDriver

class PkgManager(Enum):
    opkg = 1
    apk = 2


@target_factory.reg_driver
@attr.s(eq=False)
class OpenWrtPackageDriver(Driver):
    """
    OpenWrtPackageDriver is meant as a driver for OpenWrt's package manager.
    This driver works independently of opkg or apk.  First a check to see if
    opkg is installed, then check if apk is installed.
    
    So far the following actions are supported in opkg nomenclature:
    - install
    - remove
    - upgrade
    - files
    - list-installed
    - update
    - search

    """
    bindings = { "shell": ShellDriver, }

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        self.cmd = None

        _, _, error = self.shell.run("which opkg")
        if error == 0:
            self.cmd = PkgManager.opkg
        
        _, _, error = self.shell.run("which apk")
        if error == 0:
            self.cmd = PkgManager.apk

        if self.cmd == None:
            raise ExecutionError("Unable to determine package manger on target device")

    def on_deactivate(self):
        pass

    @Driver.check_active
    @step(args=['pkgname'])
    def list_installed(self, pkgname = "*"):
        if self.cmd == PkgManager.opkg:
            result, _, _ = self.shell.run(f"""opkg list-installed "{pkgname}" """)
            return result
        elif self.cmd == PkgManager.apk:
            result, _, error = self.shell.run(f"""apk list --installed "{pkgname}" """)
            return result
