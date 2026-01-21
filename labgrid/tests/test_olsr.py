import pytest

@pytest.mark.lg_feature("olsr")
def test_olsr_installed(package_manager):
    result = package_manager.list_installed("olsrd")
    assert "olsrd" in " ".join(result)

@pytest.mark.lg_feature("olsr")
def test_olsr_pid(shell_command):
    pid, _, _ = shell_command.run("cat /tmp/run/olsrd.pid")
    _, _ ,running = shell_command.run(f"""test -d /proc/{pid[0]}""")

    assert int(pid[0]) > 0
    assert running == 0

@pytest.mark.lg_feature("olsr")
def test_olsr_jsoninfo(shell_command):
    version, _, errorcode = shell_command.run("echo /version | nc 127.0.0.1 9090")
    assert len(version[0]) > 0
    assert errorcode == 0

