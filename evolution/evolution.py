import asyncio
import json
import time
from math import floor

import board
import busio
import digitalio
import RPi.GPIO as GPIO
import websockets
from adafruit_max31865 import MAX31865
from simple_pid import PID

from evolution.state import load_state, save_state


class Evolution:
    def __init__(self, boiler_pin, steam_pin, heater_pin, pump_pin, wait=1) -> None:
        self.clients = set()
        self.state = load_state("state.json")
        self.pid = PID(
            self.state["kp"],
            self.state["ki"],
            self.state["kd"],
            setpoint=pid_target(self.state),
            output_limits=(0, 100),
        )
        self.wait = wait
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.boiler = sensor(boiler_pin)
        self.steam = sensor(steam_pin)
        self.heater = ssr(heater_pin)
        self.pump = ssr(pump_pin)
        self.pump_task = asyncio.Task(asyncio.sleep(0))

    async def pump_run(self, pwm, duration=None):
        self.pump.ChangeDutyCycle(pwm)
        await publish_event(self.clients, "pump", {"pwm": pwm, "duration": duration})
        if duration and duration > 0:
            await asyncio.sleep(duration)
            self.pump.ChangeDutyCycle(0)
            await publish_event(self.clients, "pump", {"pwm": 0, "duration": None})

    async def pump_handler(self, on):
        if not on:
            await self.pump_run(0)
            return

        preinf = self.state["preinf"] * self.state["preinfOn"]
        if preinf > 0:
            await self.pump_run(20, preinf)

        timer = self.state["timer"] * self.state["timerOn"]
        if timer > 0:
            await self.pump_run(100, timer)
            self.state["pumpOn"] = False
            await publish_event(self.clients, "state", self.state)
        else:
            await self.pump_run(100)

    async def heater_handler(self):
        while True:
            stats = heater_stats(self.boiler, self.steam, self.pid, self.state)
            self.heater.ChangeDutyCycle(stats["heater_pwm"])
            await publish_event(self.clients, "stats", stats)
            await asyncio.sleep(self.wait)

    async def websocket_handler(self, websocket, _):
        self.clients.add(websocket)
        try:
            await websocket.send(event("state", self.state))
            async for message in websocket:
                data = json.loads(message)
                action = data["action"]
                value = data["value"]
                self.state[action] = value
                self.pid.setpoint = pid_target(self.state)
                self.pid.tunings = (
                    self.state["kp"],
                    self.state["ki"],
                    self.state["kd"],
                )

                if action == "pumpOn":
                    if not self.pump_task.done():
                        self.pump_task.cancel()
                    self.pump_task = asyncio.create_task(self.pump_handler(value))

                await publish_event(self.clients, "state", self.state)
        finally:
            self.clients.remove(websocket)

    def run(self):
        try:
            start_server = websockets.serve(self.websocket_handler, "127.0.0.1", 6789)
            asyncio.get_event_loop().run_until_complete(
                asyncio.wait([start_server, self.heater_handler()])
            )
        except KeyboardInterrupt:
            print("Exiting on KeyboardInterrupt.")
        except Exception as ex:
            print(f"Exiting on unhandled exeption: '{ex}'.")
        finally:
            GPIO.cleanup()
            save_state(self.state)


def heater_stats(boiler, steam, pid, state):
    steam_temp = steam.temperature
    boiler_temp = boiler.temperature
    actual_temp = steam_temp if state["steamOn"] else boiler_temp
    duty_cycle = pid(actual_temp)

    stats = {
        "steam_temp": steam_temp,
        "boiler_temp": boiler_temp,
        "heater_pwm": duty_cycle,
        "time": floor(time.time() * 1000),
    }

    return stats


def pid_target(state):
    if state["steamOn"] is False and state["boilOn"] is False:
        return -240

    if state["steamOn"] and state["boilOn"] is False:
        return state["steam"]

    return state["boil"]


def sensor(pin):
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(getattr(board, f"D{pin}"))
    return MAX31865(spi, cs, wires=2)


def ssr(pin):
    GPIO.setup(pin, GPIO.OUT)
    ssr = GPIO.PWM(pin, 50)
    ssr.start(0)
    return ssr


def event(type, data):
    return json.dumps({"type": type, **data})


async def publish_event(clients, type, data):
    if clients:
        json_data = json.dumps({"type": type, **data})
        await asyncio.wait([client.send(json_data) for client in clients])


if __name__ == "__main__":
    evo = Evolution(5, 6, 16, 26)
    evo.run()
