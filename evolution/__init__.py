__version__ = "0.1.0"

import configparser
import multiprocessing as mp
import os
import sys
from time import sleep

from evolution.controller import controller
from evolution.ssr import ssr
from evolution.temperature import temperature
from evolution.store import store


def run():
    print(f"[evolution] Starting.")

    config_parser = configparser.ConfigParser()
    config_parser.read("./config.ini")
    config = config_parser["evolution"]

    children = []

    # Sensor publisher.
    children.append(
        mp.Process(
            target=temperature,
            args=(
                int(config["TemperatureBoilerPin"]),
                int(config["TemperatureSteamPin"]),
                int(config["TemperaturePort"]),
            ),
            daemon=True,
        )
    )

    # Ssr subscriber.
    children.append(
        mp.Process(
            target=ssr,
            args=(
                int(config["SsrBoilerPin"]),
                int(config["SsrPumpPin"]),
                int(config["SsrPort"]),
            ),
            daemon=True,
        )
    )

    # Constroller publisher/subscriber.
    children.append(
        mp.Process(
            target=controller,
            args=(
                int(config["TemperaturePort"]),
                int(config["SsrPort"]),
                int(config["PidPort"]),
                float(config["PidTarget"]),
                float(config["PidKp"]),
                float(config["PidKi"]),
                float(config["PidKd"]),
            ),
            daemon=True,
        )
    )

    children.append(
        mp.Process(
            target=store,
            args=(
                [
                    int(config["TemperaturePort"]),
                    int(config["SsrPort"]),
                    int(config["PidPort"]),
                ],
            ),
            daemon=True,
        )
    )

    # Run forever until interuption.
    try:
        for child in children:
            child.start()

        print(f"[evolution] Processes started.")

        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("[evolution] KeyboardInterrupt.")
    except Exception as ex:
        print(f"[evolution] unhandled exception: {ex}")
        for child in mp.active_children():
            child.terminate()
    finally:
        print("[evolution] exit.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
