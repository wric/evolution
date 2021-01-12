from unittest.mock import ANY, Mock, call, mock_open, patch

import pytest
from evolution.state import (
    DEFAULT_STATE,
    State,
    UnsupportedState,
    load_state,
    save_state,
)


def test_load_state_returns_default_state():
    assert load_state(None) == DEFAULT_STATE


def test_load_state_returns_default_state_on_nonexisting_path():
    path = "foobar"
    mock_file = Mock(side_effect=FileNotFoundError)

    with patch("builtins.open", mock_file):
        state = load_state(path)

    mock_file.assert_called_once()
    assert mock_file.call_args_list == call((path, "r"))
    assert state == DEFAULT_STATE


def test_load_state_returns_saved_state():
    path = ".\save\state.json"
    json_state = '{"boil": 25, "pumpOn": true}'
    mock_file = mock_open(read_data=json_state)

    with patch("builtins.open", mock_file):
        state = load_state(path)

        mock_file.assert_called_once()
        assert mock_file.call_args_list == call((path, "r"))
        assert state == {"boil": 25, "pumpOn": True}


def test_save_state_without_path_doesnt_throw():
    mock_print = Mock()

    with patch("builtins.print", mock_print):
        state = load_state(None)
        save_state(state)

    mock_print.assert_called_once_with("No filepath to save state to.")


def test_save_state_saves_state():
    path = ".\save\state.json"
    state_dict = {"boil": 25, "pumpOn": True}
    mock_file = mock_open()
    mock_json = Mock()
    state = State(save_path=path, **state_dict)

    with patch("json.dump", mock_json):
        with patch("builtins.open", mock_file):
            save_state(state)

    mock_file.assert_called_once_with(path, "w")
    mock_json.assert_called_once_with(state_dict, ANY, indent=4)


def test_state_invalid_key_raises_exception():
    state = load_state(None)

    with pytest.raises(UnsupportedState) as ex:
        state["invalid_set"] = "fail"
        assert "Invalid key: invalid_set." == str(ex)

        state["invalid_get"]
        assert "Invalid key: invalid_get." == str(ex)


def test_set_boilOn_True_disables_steamOn():
    state = State({"boilOn": True, "steamOn": False}, save_path="")
    state["boilOn"] = True
    assert state["boilOn"] is True
    assert state["steamOn"] is False


def test_set_steamOn_True_disables_boilOn():
    state = State({"boilOn": True, "steamOn": False}, save_path="")
    state["steamOn"] = True
    assert state["boilOn"] is False
    assert state["steamOn"] is True


def test_set_boilOn_False_doesnt_enable_steamOn():
    state = State({"boilOn": True, "steamOn": False}, save_path="")
    state["boilOn"] = False
    assert state["boilOn"] is False
    assert state["steamOn"] is False
