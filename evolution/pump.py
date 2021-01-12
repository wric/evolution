import asyncio
from dataclasses import asdict, dataclass

from evolution.common import ssr

PWM_BREW = 100
PWM_PREINF = 20
PWM_OFF = 0
ONE_HOUR = 3600


class Pump:
    def __init__(self, pump_pin):
        self.ssr = ssr(pump_pin)
        self.task = asyncio.Task(asyncio.sleep(0))

    def run(self, state, callback):
        if not self.task.done():
            self.task.cancel()

        self.task = asyncio.create_task(run_pump(self.ssr, state, callback))


@dataclass
class Run:
    pwm: int
    duration: float


async def run_pump(ssr, state, callback):
    for run in evaluate_runs(state):
        ssr.ChangeDutyCycle(run.pwm)
        await callback(asdict(run))
        await asyncio.sleep(run.duration)

    await callback("off")


def evaluate_runs(state):
    pump_off = Run(PWM_OFF, 0)

    if not state["pumpOn"]:
        return [pump_off]

    runs = []
    if state["preinfOn"]:
        runs += [Run(PWM_PREINF, state["preinf"]), pump_off]

    if state["timerOn"]:
        runs += [Run(PWM_BREW, state["timer"]), pump_off]
    else:
        runs.append(Run(PWM_BREW, ONE_HOUR))

    return runs
