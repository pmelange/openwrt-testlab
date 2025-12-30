import pytest

def test_uptime(configured):
    _, _, errorcode = configured.run('uptime')
    assert errorcode == 0

