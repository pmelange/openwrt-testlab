import os
import enum
from enum import auto

import attr

from labgrid import Environment, Target
from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError
from labgrid.util import Timeout
from labgrid.util.ssh import sshmanager
from labgrid.step import step
from labgrid.resource import NetworkService
from labgrid.driver import SSHDriver

from time import sleep

class Status(enum.Enum):
    unknown = auto()
    off = auto()
    on = auto()
    shell = auto()

@target_factory.reg_driver
@attr.s(eq=False)
class TestStrategy(Strategy):
    """OpenWrtFlashBootStrategy - Strategy to boot from flash"""
    bindings = {
        #"ssh": SSHDriver
            }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @step(args=['status'])
    def transition(self, status):
        if not isinstance(status, Status):
            status = Status[status]

        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")

        elif status == self.status:
            return # nothing to do

        elif status == Status.off:
            print("Status off")

        elif status == Status.on:
            print("transition to off")
            self.transition(Status.off)
            print("Status on")
        
        elif status == Status.shell:
            env = self.target.env
            target = env.get_target("dut")
            target.activate(self, "dut")
            #ns = target.get_resource("NetworkService", "altserv")
            #target.bin_resource(ns)
            ns = NetworkService(target, "altserv", "10.36.198.225", "root")
            #target.bind_resource(ns)
            [ubk] = SSHDriver.bindings
            target.set_binding_map({ubk: "altserv"})
            print(target.resources)
            ssh = SSHDriver(target, "altserv")#.get_driver("SSHDriver", resource=ns)
            target.activate(ssh)
            result, _, _ = ssh.run("uname -a")
            print(result)
            pass

        self.status = status

