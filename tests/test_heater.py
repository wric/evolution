from unittest.mock import Mock, patch

import pytest
from evolution.heater import evalute_setpoint, js_timestamp, run_heater

mock_time = Mock(return_value=1610302227.488837)


@pytest.fixture
def mock_heater():
    class MockHeater:
        boiler = Mock(temperature=94.3)
        steam = Mock(temperature=115.5)
        ssr = Mock(ChangeDutyCycle=Mock())
        pid = Mock(return_value=92.3)

    return MockHeater()


@patch("time.time", mock_time)
def test_js_timestamp():
    assert js_timestamp() == 1610302227488


@patch("time.time", mock_time)
def test_run_heater(mock_heater):
    expected = {
        "steam_temp": 115.5,
        "boiler_temp": 94.3,
        "heater_pwm": 92.3,
        "time": 1610302227488,
    }

    assert run_heater(mock_heater, False) == expected
    mock_heater.pid.assert_called_once_with(expected["boiler_temp"])
    mock_heater.ssr.ChangeDutyCycle.assert_called_once_with(expected["heater_pwm"])


def test_run_heater_uses_steam_when_steam_on(mock_heater):
    steam_temp = 115.5
    run_heater(mock_heater, True)
    mock_heater.pid.assert_called_once_with(steam_temp)


def test_evalute_setpoint_return_boil_when_boilOn():
    state = {"steamOn": False, "steam": 130, "boilOn": True, "boil": 90}
    assert evalute_setpoint(state) == state["boil"]


def test_evalute_setpoint_return_steam_when_steamOn():
    state = {"steamOn": True, "steam": 130, "boilOn": False, "boil": 90}
    assert evalute_setpoint(state) == state["steam"]


def test_evalute_setpoint_return_negative_240_when_no_on():
    state = {"steamOn": False, "steam": 130, "boilOn": False, "boil": 90}
    assert evalute_setpoint(state) == -240


def test_evalute_setpoint_return_boil_if_both_on():
    state = {"steamOn": True, "steam": 130, "boilOn": True, "boil": 90}
    assert evalute_setpoint(state) == state["boil"]
