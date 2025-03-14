import os
import enum
from enum import auto

import attr

from labgrid.factory import target_factory
from labgrid.strategy import Strategy, StrategyError
from labgrid.util import Timeout
from labgrid.util.ssh import sshmanager
from labgrid.step import step

from time import sleep

class Status(enum.Enum):
    unknown = auto()
    off = auto()
    on = auto()

@target_factory.reg_driver
@attr.s(eq=False)
class TestStrategy(Strategy):
    """OpenWrtFlashBootStrategy - Strategy to boot from flash"""
    bindings = {
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
        
        self.status = status

