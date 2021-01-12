import asyncio
from unittest.mock import Mock, call, patch

import pytest
from evolution.common import ssr
from evolution.pump import Pump, Run, evaluate_runs, run_pump
from evolution.state import DEFAULT_STATE


class AsyncMock(Mock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.fixture
def state():
    state = DEFAULT_STATE
    state["pumpOn"] = True
    return state


def test_evaluate_runs_stop_when_pumpOn_False(state):
    state["pumpOn"] = False
    assert evaluate_runs(state) == [Run(0, 0)]


def test_evaluate_runs_on_forever_when_no_timers(state):
    state["timerOn"] = False
    state["preinfOn"] = False
    assert evaluate_runs(state) == [Run(100, 3600)]


def test_evaluate_runs_timerOn_returns_time_limited(state):
    state["timerOn"] = True
    state["timer"] = 25
    state["preinfOn"] = False
    assert evaluate_runs(state) == [Run(100, state["timer"]), Run(0, 0)]


def test_evaluate_runs_timerOn_and_preinfOn_returns_doubble_time_limited(state):
    state["timerOn"] = True
    state["timer"] = 25
    state["preinfOn"] = True
    state["preinf"] = 5
    assert evaluate_runs(state) == [
        Run(20, state["preinf"]),
        Run(0, 0),
        Run(100, state["timer"]),
        Run(0, 0),
    ]


def test_evaluate_runs_timerOn_returns_time_limited_preinf_then_runs_forever(state):
    state["timerOn"] = False
    state["preinfOn"] = True
    state["preinf"] = 5
    assert evaluate_runs(state) == [
        Run(20, state["preinf"]),
        Run(0, 0),
        Run(100, 3600),
    ]


@pytest.mark.asyncio
async def test_run_pump_with_end(state):
    state["timerOn"] = True
    state["timer"] = 25
    state["preinfOn"] = False

    callback = AsyncMock()
    mock_sleep = AsyncMock()
    ssr = Mock(ChangeDutyCycle=Mock())

    with patch("asyncio.sleep", mock_sleep):
        await run_pump(ssr, state, callback)

    assert mock_sleep.call_args_list == [call(25), call(0)]
    assert ssr.ChangeDutyCycle.call_args_list == [call(100), call(0)]
    assert callback.call_args_list == [
        call({"pwm": 100, "duration": 25}),
        call({"pwm": 0, "duration": 0}),
        call("off"),
    ]


@pytest.mark.asyncio
async def test_Pump_run_is_cancelable(state):
    class MockPump(Pump):
        def __init__(self):
            self.ssr = Mock(ChangeDutyCycle=Mock())
            self.task = asyncio.Task(asyncio.sleep(0))

    state["timerOn"] = True
    state["timer"] = 60
    state["preinfOn"] = False
    pump = MockPump()

    callback = AsyncMock()
    pump.run(state, callback)

    # We must give it some time to execute.
    await asyncio.sleep(0.1)

    assert pump.task.done() is False
    pump.ssr.ChangeDutyCycle.assert_called_once_with(100)
    callback.assert_called_once_with({"pwm": 100, "duration": 60})

    state["pumpOn"] = False
    pump.run(state, callback)

    await asyncio.sleep(0.1)

    assert pump.ssr.ChangeDutyCycle.call_args_list == [call(100), call(0)]
    assert callback.call_args_list == [
        call({"pwm": 100, "duration": 60}),
        call({"pwm": 0, "duration": 0}),
        call("off"),
    ]
