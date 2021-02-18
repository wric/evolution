# Simple listener utility to listen to the websocket communication.
# Based on client example from: https://websockets.readthedocs.io/en/stable/intro.html

import json

import websockets


async def listener(uri, handler_fn, topics):
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if topics and data["topic"] not in topics:
                return

            handler_fn(data)
