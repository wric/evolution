import asyncio
import json

import RPi.GPIO as GPIO
import websockets

from evolution.heater import Heater
from evolution.pump import Pump
from evolution.state import load_state, save_state


class Evolution:
    clients = set()

    def __init__(
        self,
        state_path,
        boiler_pin,
        steam_pin,
        heater_pin,
        pump_pin,
        update_interval=1,
    ):
        self.state = load_state(state_path)
        self.pump = Pump(pump_pin)
        self.heater = Heater(boiler_pin, steam_pin, heater_pin)
        self.heater.tune(self.state)
        self.update_interval = update_interval

    async def websocket_handler(self, websocket, _):
        self.clients.add(websocket)
        try:
            await websocket.send(event("state", self.state))
            async for message in websocket:
                await self.message_handler(message)
        finally:
            self.clients.remove(websocket)

    async def message_handler(self, message):
        action, value = json.loads(message).values()
        self.state[action] = value

        if action == "pumpOn":
            self.pump.run(self.state, self.pump_callback)

        if action in ("kp", "ki", "kd", "boil", "steam"):
            self.heater.tune(self.state)

        await self.send_message("state", self.state)

    async def heater_handler(self):
        while True:
            stats = self.heater.run(self.state["steamOn"])
            await send_message(self.clients, "stats", stats)
            await asyncio.sleep(self.update_interval)

    async def pump_callback(self, data):
        if data != "off":
            await self.send_message("pump", data)
            return

        self.state["pumpOn"] = False
        await self.send_message("state", self.state)

    async def send_message(self, *args):
        await send_message(self.clients, *args)


async def send_message(clients, topic, data):
    if not clients:
        return

    message = event(topic, data)
    await asyncio.wait([ws.send(message) for ws in clients])


def event(topic, data):
    return json.dumps({"topic": topic, **data})


def main():
    evo = Evolution("state.json", 5, 6, 16, 26, 1)
    server = websockets.serve(evo.websocket_handler, "127.0.0.1", 6789)

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


if __name__ == "__main__":
    main()
