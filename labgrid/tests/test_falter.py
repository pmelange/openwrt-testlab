import pytest
import re
import json
from time import sleep

@pytest.mark.lg_feature(["falter", "online"])
def test_ffuplink_initialized(ffwizard, shell_command):
    count = 0
    while count < 10:
        _, _, errorcode = shell_command.run("ubus -t 10 wait_for network.interface.ffuplink")
        if errorcode == 0:
            result, _, _ = shell_command.run("ubus call network.interface.ffuplink status")
            data = json.loads(" ".join(result))
            if data["up"] == True:
                break
        count += 1
        sleep(10)
    assert count < 10
    assert errorcode == 0
    assert data["up"] == True

@pytest.mark.lg_feature(["falter", "online"])
def test_ffuplink_up(ffwizard, shell_command):
    result, _, errorcode = shell_command.run("ip addr show dev ffuplink")
    assert "UP" in result[0]

    try:
        ipaddr = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' '.join(result)).group()
    except:
        ipaddr = None
    assert ipaddr is not None

@pytest.mark.lg_feature(["falter", "online"])
def test_ffuplink_ping_dot8(ffwizard, shell_command):
    _, _, errorcode = shell_command.run("ping -c 3 -I ffuplink 8.8.8.8")
    assert errorcode == 0

