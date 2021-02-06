from unittest.mock import Mock

import pytest
from evolution import __version__
from evolution.evolution import event


class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


def test_version():
    assert __version__ == "0.1.0"


def test_event():
    topic = "test"
    data = {"a": 10, "b": 9.9, "c": "data"}
    expected = '{"topic": "test", "a": 10, "b": 9.9, "c": "data"}'
    assert event(topic, data) == expected
