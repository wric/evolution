import sqlite3

from flask import Flask, g, jsonify

from evolution.store import init_connection

app = Flask(__name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = init_connection()
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/")
def hello_world():
    return "ok"


@app.route("/api/<component>", methods=["GET"])
def api_component(component):
    return component


@app.route("/api/<component>/<scope>", methods=["GET"])
def api_component_scope(component, scope):
    query = (
        "SELECT * "
        "FROM [events] "
        "WHERE [topic] = ?"
        "AND [inserted_at] > datetime('now','-15 seconds')"
    )
    res = query_db(query, (f"{component}:{scope}",))
    return jsonify([dict(row) for row in res])


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
