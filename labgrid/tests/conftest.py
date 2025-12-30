import pytest

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
@pytest.mark.lg_feature("ffwizard")
def ffwizard(strategy, configured):
    try:
        strategy.transition("ffwizard")
        return configured
    except Exception:
        pytest.exit("Failed to transition to state ffwizard", returncode=3)

@pytest.fixture(scope="session")
@pytest.mark.lg_feature("ramboot")
def load_target(strategy):
    try:
        strategy.transition("ramboot")
        return strategy
    except Exception:
        pytest.exit("Failed to transition to state ramboot", returncode=3)

@pytest.fixture(scope="session")
@pytest.mark.lg_feature("flash")
def load_target(strategy):
    try:
        strategy.transition("flash")
        return strategy
    except Exception:
        pytest.exit("Failed to transition to state flash", returncode=3)

@pytest.fixture(scope="session")
@pytest.mark.lg_feature("ramboot_then_flash")
def load_target(strategy):
    try:
        strategy.transition("flash")
        return strategy
    except Exception:
        pytest.exit("Failed to transition to state flash via ramboot", returncode=3)
