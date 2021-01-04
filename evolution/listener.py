# Simple listener utility to listen to the websocket communication.
# Based on client example from: https://websockets.readthedocs.io/en/stable/intro.html

import asyncio
import json
import sys

import websockets


async def listener(uri, handler_fn, topics):
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if topics and data["topic"] not in topics:
                return

            handler_fn(data)


if __name__ == "__main__":
    args = sys.argv
    uri = "127.0.0.1:6789" if len(args) == 0 else args[0]
    topics = [] if len(args) < 2 else args[1].split(",")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(listener(uri, print, topics))
    loop.run_forever()
