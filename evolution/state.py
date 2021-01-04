import json
from collections import UserDict

DEFAULT_STATE = {
    "boil": 94,
    "boilOn": False,
    "steam": 135.0,
    "steamOn": False,
    "state": "boil",
    "timer": 2,
    "timerOn": False,
    "preinf": 2,
    "preinfOn": False,
    "kp": 4.2,
    "ki": 0.5,
    "kd": 0.12,
    "pumpOn": False,
}


class UnsupportedState(Exception):
    pass


class State(UserDict):
    """ A modified dict to handle the machine state.
        Should probably be re-written as a real object.
    """
    def __init__(self, *args, save_path="", **kwargs):
        super().__init__(*args, **kwargs)
        self.save_path = save_path

    def __setitem__(self, key, value):
        self._validate_key(key)
        super().__setitem__(key, value)

        if key == "boilOn" and value is True:
            super().__setitem__("steamOn", False)
        if key == "steamOn" and value is True:
            super().__setitem__("boilOn", False)

    def __getitem__(self, key):
        self._validate_key(key)
        return super().__getitem__(key)

    def _validate_key(self, key):
        if key not in DEFAULT_STATE.keys():
            raise UnsupportedState(f"Invalid key: {key}.")


def load_state(save_path):
    if not save_path:
        return State(DEFAULT_STATE)

    try:
        with open(save_path, "r") as file:
            return State(json.load(file), save_path=save_path)
    except FileNotFoundError:
        return State(DEFAULT_STATE, save_path=save_path)


def save_state(state):
    if not state.save_path:
        print("No filepath to save state to.")
        return

    with open(state.save_path, "w") as file:
        json.dump(dict(state), file, indent=4)
