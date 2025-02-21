import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURR_DIR)

from strategy.covrflashbootstrategy import CovrFlashBootStrategy
from strategy.covrubootstrategy import CovrUBootStrategy
from driver.covrubootdriver import CovrSmallUBootDriver
from driver.openwrtucidriver import OpenwrtUciDriver
