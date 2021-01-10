import time
from math import floor

from simple_pid import PID

from evolution.common import sensor, ssr


class Heater:
    def __init__(self, boiler_pin, steam_pin, heater_pin):
        self.boiler = sensor(boiler_pin)
        self.steam = sensor(steam_pin)
        self.ssr = ssr(heater_pin)
        self.pid = PID(output_limits=(0, 100))

    def run(self, steam_on):
        return run_heater(self, steam_on)

    def tune(self, state):
        tune_pid(state, self.pid)


def run_heater(heater, steam_on):
    steam_temp = heater.steam.temperature
    boiler_temp = heater.boiler.temperature
    actual_temp = steam_temp if steam_on else boiler_temp
    duty_cycle = heater.pid(actual_temp)
    heater.ssr.ChangeDutyCycle(duty_cycle)

    return {
        "steam_temp": steam_temp,
        "boiler_temp": boiler_temp,
        "heater_pwm": duty_cycle,
        "time": js_timestamp(),
    }


def js_timestamp():
    return floor(time.time() * 1000)


def tune_pid(state, pid):
    pid.setpoint = evalute_setpoint(state)
    pid.tunings = (
        state["kp"],
        state["ki"],
        state["kd"],
    )


def evalute_setpoint(state):
    if state["steamOn"] is False and state["boilOn"] is False:
        return -240

    if state["steamOn"] and state["boilOn"] is False:
        return state["steam"]

    return state["boil"]
