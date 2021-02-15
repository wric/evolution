import asyncio
import json

import RPi.GPIO as GPIO
import zmq
import zmq.asyncio

from evolution.heater import Heater
from evolution.pump import Pump
from evolution.state import load_state, save_state


class Evolution:
    def __init__(
        self,
        state_path,
        boiler_pin,
        steam_pin,
        heater_pin,
        pump_pin,
        pub_port,
        sub_port,
        update_interval=1,
    ):
        self.state = load_state(state_path)
        self.pump = Pump(pump_pin)
        self.heater = Heater(boiler_pin, steam_pin, heater_pin)
        self.heater.tune(self.state)
        self.update_interval = update_interval

        context = zmq.asyncio.Context.instance()
        self.publisher = context.socket(zmq.PUB)
        self.publisher.bind(f"tcp://127.0.0.1:{pub_port}")
        self.subscriber = context.socket(zmq.XSUB)
        self.subscriber.connect(f"tcp://127.0.0.1:{sub_port}")
        self.subscriber.subscribe("")

    async def message_handler(self, message):
        action, value = message.values()
        self.state[action] = value

        if action == "pumpOn":
            self.pump.run(self.state, self.pump_callback)

        if action in ("kp", "ki", "kd", "boil", "steam"):
            self.heater.tune(self.state)

        await self.send_message("state", self.state)

    async def heater_handler(self):
        while True:
            stats = self.heater.run(self.state["steamOn"])
            await self.send_message("stats", stats)
            await asyncio.sleep(self.update_interval)

    async def subscriber_handler(self):
        while True:
            message = await self.subscriber.recv_json()
            await self.message_handler(message)

    async def pump_callback(self, data):
        if data == "off":
            self.state["pumpOn"] = False
            await self.send_message("state", self.state)
        else:
            await self.send_message("pump", data)

    async def send_message(self, topic, data):
        message = {"topic": topic, **data}
        await self.publisher.send_json(message)


def main():
    evo = Evolution("state.json", 5, 6, 16, 26, 5550, 5560, 1)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.wait([evo.subscriber_handler(), evo.heater_handler()])
        )
    except KeyboardInterrupt:
        print("Exiting on KeyboardInterrupt.")
    except Exception as ex:
        print(f"Exiting on unhandled exeption: '{ex}'.")
    finally:
        GPIO.cleanup()
        save_state(evo.state)


if __name__ == "__main__":
    main()
