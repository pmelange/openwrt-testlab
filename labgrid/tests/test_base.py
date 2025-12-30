import pytest

def test_uptime(configured, shell_command):
    _, _, errorcode = shell_command.run('uptime')
    assert errorcode == 0

def test_ping_from_exporter(lan_ip, configured, exporter_command):
    _, _, errorcode = exporter_command.run(f"ping -c 5 {lan_ip}")
    assert errorcode == 0

def test_ping_first_dhcp_lease(configured, shell_command):
    _, _, errorcode = shell_command.run("ping -c 5 $(head -1 /tmp/dhcp.leases | cut -d ' ' -f 3)")

