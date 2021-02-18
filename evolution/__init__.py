import asyncio
import json

import RPi.GPIO as GPIO
import websockets

from evolution.evolution import Evolution
from evolution.listener import listener
from evolution.state import save_state

__version__ = "0.1.0"


def main():
    config = get_config()

    evo = Evolution(
        "state.json",
        config["boiler_pin"],
        config["steam_pin"],
        config["heater_pin"],
        config["pump_pin"],
        config["update_interval"],
    )

    server = websockets.serve(
        evo.websocket_handler, "127.0.0.1", config["websocket_port"]
    )

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([server, evo.heater_handler()]))
    except KeyboardInterrupt:
        print("Exiting on KeyboardInterrupt.")
    except Exception as ex:
        print(f"Exiting on unhandled exeption: '{ex}'.")
    finally:
        GPIO.cleanup()
        save_state(evo.state)


def printer():
    config = get_config()
    uri = f"127.0.0.1:{config['websocket_port']}"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listener(uri, print, []))
    loop.run_forever()


def get_config():
    with open("config.json", "r") as config:
        return json.load(config)
