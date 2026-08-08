"""Safe Flask fixture — the correct variant of every vuln in vuln.py.

GREEN bed: each rule that FIRES on the matching vuln.py sink must stay SILENT
here. Same routes, same entry points, sinks sanitized. Ground truth: ../MANIFEST.md.
"""

import os
import subprocess
from urllib.parse import urlparse

import requests
import yaml
from flask import Flask, abort, request, session

app = Flask(__name__)

ORDERS = {"1": {"owner": "alice", "total": 42}, "2": {"owner": "bob", "total": 99}}
ALLOWED_HOSTS = {"api.internal.example"}
DATA_DIR = "/var/data"


def _current_user():
    return session.get("user")


@app.route("/order")
def get_order():
    # SAFE CWE-89 — parameterized query, no interpolation.
    order_id = request.args["id"]
    cur = _db().cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))  # SAFE:CWE-89
    return str(cur.fetchall())


@app.route("/ping")
def ping():
    # SAFE CWE-78 — argument vector, no shell, host validated.
    host = request.args["host"]
    if not host.replace(".", "").isalnum():
        abort(400)
    out = subprocess.run(["ping", "-c", "1", host], capture_output=True)  # SAFE:CWE-78
    return out.stdout


@app.route("/fetch")
def fetch():
    # SAFE CWE-918 — host allowlist before the outbound request.
    url = request.args["url"]
    if urlparse(url).hostname not in ALLOWED_HOSTS:
        abort(403)
    return requests.get(url, timeout=5).text  # SAFE:CWE-918


@app.route("/download")
def download():
    # SAFE CWE-22 — basename strips traversal; join stays under DATA_DIR.
    name = os.path.basename(request.args["name"])
    with open(os.path.join(DATA_DIR, name)) as fh:  # SAFE:CWE-22
        return fh.read()


@app.route("/config", methods=["POST"])
def load_config():
    # SAFE CWE-502 — SafeLoader refuses arbitrary object construction.
    return str(yaml.safe_load(request.data))  # SAFE:CWE-502


@app.route("/orders/<order_id>")
def read_order(order_id):
    # SAFE CWE-639 — ownership check against the session user before returning.
    order = ORDERS.get(order_id)
    if order is None or order["owner"] != _current_user():
        abort(404)
    return str(order)  # SAFE:CWE-639


@app.route("/admin/delete")
def admin_delete():
    # SAFE CWE-287 — authorization gate before the privileged action.
    if _current_user() != "admin":
        abort(403)
    target = request.args["user"]
    return f"deleted {target}"  # SAFE:CWE-287


def _db():
    import sqlite3

    return sqlite3.connect(":memory:", check_same_thread=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081)  # local bind
