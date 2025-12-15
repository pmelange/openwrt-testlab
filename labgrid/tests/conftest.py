import pytest

@pytest.fixture
def shell_command(strategy):
    try:
        strategy.transition("shell")
        return strategy.shell
    except Exception:
        pytest.exit("Failed to transition to state shell", returncode=3)

@pytest.fixture
def configured(strategy, shell_command):
    try:
        strategy.transition("confige")
        return shell_command
    except Exception:
        pytest.exit("Failed to transition to state configure", returncode=3)

