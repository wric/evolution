import sqlite3

import zmq

from evolution.utils import worker, worker_main_loop

DB_PATH = "/home/pi/Src/evolution/evolution.db"


@worker
def store(ports, db_path=DB_PATH):
    connection = init_connection(db_path)
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for port in ports:
        subscriber.connect(f"tcp://127.0.0.1:{port}")

    subscriber.subscribe("")

    def finally_fn():
        if connection:
            connection.close()

    @worker_main_loop("store", finally_fn)
    def main_loop():
        while True:
            topic, value = subscriber.recv_string().split(" ", 1)
            connection.execute(INSERT_MESSAGE_QUERY, (topic, float(value)))
            connection.commit()

    main_loop()


def init_connection(db_path=DB_PATH):
    connection = sqlite3.connect(db_path)
    connection.execute(CREATE_EVENTS_TABLE_QUERY)
    return connection


def main():
    store([5555, 5556, 5557])


if __name__ == "__main__":
    main()


CREATE_EVENTS_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS [events] (
    [id] INTEGER PRIMARY KEY,
    [inserted_at] TIMESTAMP DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
    [topic] TEXT,
    [value] REAL
)
"""

INSERT_MESSAGE_QUERY = (
    "INSERT INTO [events] ([topic], [value]) "
    "VALUES (?, ?)"
)