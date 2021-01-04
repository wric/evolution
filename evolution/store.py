# WIP. Store all event to a sqlite db. Just need to connected to the
# `listener` module but ccurently this feature is not needed/used/implemented.

import sqlite3


def insert_event(connection, topic, value):
    connection.execute(INSERT_MESSAGE_QUERY, (topic, str(value)))
    connection.commit()


def init_connection(db_path):
    connection = sqlite3.connect(db_path)
    connection.execute(CREATE_EVENTS_TABLE_QUERY)
    return connection


CREATE_EVENTS_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS [events] (
    [id] INTEGER PRIMARY KEY,
    [inserted_at] TIMESTAMP DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
    [topic] TEXT,
    [value] TEXT
)
"""

INSERT_MESSAGE_QUERY = "INSERT INTO [events] ([topic], [value]) VALUES (?, ?)"
