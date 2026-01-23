import pytest
from time import sleep
from labgrid.util import sshmanager

# pull in some features as fixtures needed to load the target image
@pytest.fixture(scope="session")
def features(env):
    return env.get_target_features()

@pytest.fixture(scope="session")
def ramboot(features):
    return "ramboot" in features

@pytest.fixture(scope="session")
def flash(features):
    return "flash" in features

@pytest.fixture(scope="session")
def ramboot_then_flash(features):
    return "ramboot_then_flash" in features

# pull in some options
@pytest.fixture(scope="session")
def lan_ip(env, target):
    return env.config.get_target_option(target.name, "lan_ip")

@pytest.fixture(scope="session")
def lan_netmask(env, target):
    return env.config.get_target_option(target.name, "lan_netmask")

@pytest.fixture(scope="session")
def lan_vlan(env, target):
    return env.config.get_target_option(target.name, "lan_vlan")

@pytest.fixture(scope="session")
def connected_port(env, target):
    return env.config.get_target_option(target.name, "connected_port")

@pytest.fixture(scope="session")
def ports(env, target):
    return env.config.get_target_option(target.name, "ports")

@pytest.fixture(scope="session")
def cpuport(env, target):
    return env.config.get_target_option(target.name, "cpuport")

# emulate the state machine
@pytest.fixture(scope="session")
def load_target(strategy, ramboot_then_flash, flash, ramboot):
    transition = None
#    return strategy
    if ramboot_then_flash or flash:
        transition = "flash"
    if ramboot:
        transition = "ramboot"
    try:
        strategy.transition(transition)
        return strategy
    except Exception:
        pytest.exit(f"Failed to transition to state {transition}", returncode=3)

@pytest.fixture(scope="session")
def shell_command(strategy, load_target):
    try:
        strategy.transition("shell")
        return strategy.shell
    except Exception:
        pytest.exit("Failed to transition to state shell", returncode=3)

@pytest.fixture(scope="session")
def configured(strategy, shell_command):
    try:
        strategy.transition("config")
        sleep(1)
        return True
    except Exception:
        pytest.exit("Failed to transition to state config", returncode=3)

@pytest.fixture(scope="session")
def ffwizard(features, strategy, configured):
    if "falter" not in features:
        pytest.exit("ARRRRRRRRRRRH", returncode=3)
        return False
    try:
        strategy.transition("ffwizard")
        return True
    except Exception:
        pytest.exit("Failed to transition to state ffwizard", returncode=3)

@pytest.fixture(scope="session")
def ssh_command(target, configured):
    return target.get_driver("SSHDriver")

@pytest.fixture(scope="session")
def exporter_command(target):
    net = target.get_driver("NetworkInterfaceDriver")
    return sshmanager.get(net.iface.host)

@pytest.fixture(scope="session")
def package_manager(target, configured):
    return target.get_driver("OpenWrtPackageDriver")

