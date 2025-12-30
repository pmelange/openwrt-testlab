import pytest

@pytest.fixture(scope="session")
def features(env):
    return (env.get_target_features())

@pytest.fixture(scope="session")
def ramboot(features):
    return ("ramboot" in features)

@pytest.fixture(scope="session")
def flash(features):
    return ("flash" in features)

@pytest.fixture(scope="session")
def ramboot_then_flash(features):
    return ("ramboot_then_flash" in features)

@pytest.fixture(scope="session")
def load_target(strategy, ramboot_then_flash, flash, ramboot):
    transition = None
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
        return shell_command
    except Exception:
        pytest.exit("Failed to transition to state config", returncode=3)

@pytest.fixture(scope="session")
def ffwizard(strategy, configured):
    try:
        strategy.transition("ffwizard")
        return configured
    except Exception:
        pytest.exit("Failed to transition to state ffwizard", returncode=3)

