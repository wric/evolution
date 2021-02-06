# Simple listener utility to listen to the zmq communication.

import asyncio

import zmq
import zmq.asyncio


async def listener(sub_port, handler_fn, topics):
    context = zmq.asyncio.Context.instance()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(f"tcp://127.0.0.1:{sub_port}")
    subscriber.subscribe("")

    while True:
        message = await subscriber.recv_json()
        if topics and message["topic"] not in topics:
            return

        handler_fn(message)


def printer():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listener("5550", print, []))
    loop.run_forever()


if __name__ == "__main__":
    printer()
