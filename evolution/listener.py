# Simple listener utility to listen to the websocket communication.
# Based on client example from: https://websockets.readthedocs.io/en/stable/intro.html

import asyncio
import sys

import zmq
import zmq.asyncio


async def listener(sub_port, handler_fn, topics):
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f"tcp://127.0.0.1:{sub_port}")

    while True:
        message = await subscriber.recv_json()
        if topics and message["topic"] not in topics:
            return

        handler_fn(message)


def main():
    args = sys.argv
    sub_port = "5550" if len(args) == 0 else args[0]
    topics = [] if len(args) < 2 else args[1].split(",")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(listener(sub_port, print, topics))
    loop.run_forever()


if __name__ == "__main__":
    main()
