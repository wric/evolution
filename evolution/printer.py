import zmq

from evolution.utils import worker, worker_main_loop


@worker
def printer(ports):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for port in ports:
        subscriber.connect(f"tcp://127.0.0.1:{port}")

    subscriber.subscribe("")

    @worker_main_loop("printer", None)
    def main_loop():
        while True:
            message = subscriber.recv_string()
            topic, value = message.split(" ", 1)
            print(f"{topic} > {value}")

    main_loop()


def main():
    printer([5555, 5556, 5557])


if __name__ == "__main__":
    main()
