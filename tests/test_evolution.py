from unittest.mock import Mock

import pytest
from evolution import __version__
from evolution.evolution import event, send_message


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


@pytest.mark.asyncio
async def test_send_message_with_no_clients():
    clients = set()
    assert await send_message(clients, None, None) is None


@pytest.mark.asyncio
async def test_send_message_sends_to_multiple_clients():
    ws1 = type("", (), {})()
    ws1.send = AsyncMock()

    ws2 = type("", (), {})()
    ws2.send = AsyncMock()

    clients = set()
    clients.add(ws1)
    clients.add(ws2)

    await send_message(clients, "test", {"a": 1})
    expected_call = '{"topic": "test", "a": 1}'

    for client in clients:
        client.send.assert_called_once_with(expected_call)
