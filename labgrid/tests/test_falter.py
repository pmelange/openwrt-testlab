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
def test_ffuplink_has_ip_addr(ffwizard, shell_command):
    result, _, errorcode = shell_command.run("ip addr show dev ffuplink")
    assert "UP" in result[0]

    try:
        ipaddr = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ' '.join(result)).group()
    except:
        ipaddr = None
    assert ipaddr is not None

@pytest.mark.lg_feature(["falter", "online"])
def test_ffuplink_default_route(ffwizard, shell_command):
    _, _, errorcode = shell_command.run("ip r g 8.8.8.8 oif ffuplink")
    assert errorcode == 0

@pytest.mark.lg_feature(["falter", "online"])
def test_ffuplink_ping_dot8(ffwizard, shell_command):
    _, _, errorcode = shell_command.run("ping -c 3 -I ffuplink 8.8.8.8")
    assert errorcode == 0

@pytest.mark.parametrize("iface", ["wireless0", "wireless1"])
@pytest.mark.lg_feature(["falter", "wifi"])
def test_wifi_mesh_interface(ffwizard, shell_command, iface):
    # find out which interface is associated with the iface
    result, _, errorcode = shell_command.run(f"uci show wireless | grep {iface}")
    if errorcode == 0:
        result = result[0].split('.')[1]
        result, _, errorcode = shell_command.run(f"uci get wireless.{result}.ifname")
        assert errorcode == 0
        result, _, errorcode = shell_command.run(f"iwinfo {result[0]} info")
        assert "Mode: Mesh Point" in " ".join(result)
    else:
        pytest.skip(f"Skipping test of {iface}, does not exist")
