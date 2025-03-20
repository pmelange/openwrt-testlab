import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURR_DIR)

from driver.freifunkwizarddriver import FreifunkWizardDriver
from strategy.freifunkstrategy import FreifunkStrategy
