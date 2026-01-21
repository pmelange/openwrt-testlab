import pytest

def test_uptime(configured, shell_command):
    _, _, errorcode = shell_command.run('uptime')
    assert errorcode == 0

def test_ipv4_ping_from_exporter(lan_ip, configured, exporter_command):
    _, _, errorcode = exporter_command.run(f"ping -c 3 {lan_ip}")
    assert errorcode == 0

def test_ipv4_ping_first_dhcp_lease(configured, shell_command):
    _, _, errorcode = shell_command.run("ping -c 3 $(head -1 /tmp/dhcp.leases | cut -d ' ' -f 3)")
    assert errorcode == 0

@pytest.mark.lg_feature("online")
def test_ipv4_default_route_exists(configured, shell_command):
    _, _, errorcode = shell_command.run("ip r g 8.8.8.8")
    assert errorcode == 0

@pytest.mark.lg_feature("online")
def test_ipv4_ping_default_route(configured, shell_command):
    result, _, _ = shell_command.run("ip route show table all | grep -m 1 ^default | cut -d ' ' -f 3")
    _, _, errorcode = shell_command.run(f"ping -c 3 {result[0]}")
    assert errorcode == 0

@pytest.mark.lg_feature("online")
def test_ipv4_ping_dot8(configured, shell_command):
    _, _, errorcode = shell_command.run("ping -c 3 8.8.8.8")
    assert errorcode == 0
