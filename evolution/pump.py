import asyncio
from dataclasses import asdict, dataclass

from evolution.common import ssr

PMW_BREW = 100
PMW_PREINF = 20
PMW_OFF = 0


class Pump:
    def __init__(self, pump_pin):
        self.ssr = ssr(pump_pin)
        self.task = asyncio.Task(asyncio.sleep(0))

    def run(self, state, callback=None):
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

        if callback:
            await callback(asdict(run))

        if run.duration is not None:
            await asyncio.sleep(run.duration)

    await callback("off")


def evaluate_runs(state):
    stop_pump = Run(0, 0)

    if not state["pumpOn"]:
        return [stop_pump]

    runs = []
    if state["preinfOn"]:
        runs += [Run(PMW_PREINF, state["preinf"]), stop_pump]

    if state["timerOn"]:
        runs += [Run(PMW_BREW, state["timer"]), stop_pump]
    else:
        runs.append(Run(PMW_BREW, None))

    return runs
