# Simple printer utility to listen to all websocket communication.
# Based on client example from: https://websockets.readthedocs.io/en/stable/intro.html

import asyncio
import json
import sys

import websockets


async def printer(uri, topics=[]):
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if topics and data["type"] not in topics:
                return

            print(data)


if __name__ == "__main__":
    args = sys.argv
    uri = "127.0.0.1:6789" if len(args) == 0 else args[0]
    topics = [] if len(args) < 2 else args[1].split(",")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(printer(uri, topics))
