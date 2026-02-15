import pytest
import re
import json
from time import sleep

from labgrid.util import Timeout

@pytest.fixture(scope="session")
def initialized(configured, shell_command):
    timeout = Timeout(300.0)
    while not timeout.expired:
        result, _, errorcode = shell_command.run("birdc show babel neighbors | grep ts_wg")
        if len(result) == 0 or errorcode == 1:
            sleep(15)
        else:
            break
    if len(result) == 0:
        # we have a problem setting up.
        pytest.exit("Failed to initialize bbbconfig setup", returncode=3)
    return True

@pytest.mark.lg_feature(["bbbconfig", "namespace_online"])
def test_bbbconfigs_uplink(initialized, shell_command):
    result, _, errorcode = shell_command.run("ip netns exec uplink ip a show dev ts_uplink | grep \"inet \"")

    try:
        ipaddr = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' '.join(result)).group()
    except:
        ipaddr = None
    assert ipaddr is not None

