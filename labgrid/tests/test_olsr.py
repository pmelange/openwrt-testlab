import pytest

@pytest.mark.lg_feature("olsr")
def test_olsr(strategy, target):
    strategy.transition("off")
    strategy.transition("reset")
    strategy.transition("off")
    strategy.transition("ffwizard")

    shell = strategy.shell #target.get_driver("SerialDriver")
    target.activate(shell)
    pid, _, _ = shell.run("cat /tmp/run/olsrd.pid")
    _, _ ,running = shell.run(f"""test -d /proc/{pid[0]}""")

    assert int(pid[0]) > 0
    assert running == 0
