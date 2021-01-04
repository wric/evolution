import json
import sys
from signal import SIGTERM, signal


def worker(fn):
    def wrap(*args, **kwargs):
        signal(SIGTERM, handle_sigterm)
        return fn(*args, **kwargs)

    return wrap


def handle_sigterm(*args):
    sys.exit(0)


def worker_main_loop(identifier, finally_fn):
    def wrap(fn):
        def wrapped_fn():
            try:
                fn()
            except KeyboardInterrupt:
                pass
            except Exception as ex:
                print(f"[{identifier}] unhandled exception '{ex}'.")
            finally:
                if finally_fn:
                    finally_fn()

                print(f"[{identifier}] clean exit.")

        return wrapped_fn

    return wrap


def create_message(topic, dict_):
    value = json.dumps(dict_)
    return f"{topic} {value}"


def parse_message(message):
    topic, json_value = message.split(" ", 1)
    return topic, json.loads(json_value)
