import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURR_DIR)

from strategy.bbbstrategy import BBBConfigStrategy
