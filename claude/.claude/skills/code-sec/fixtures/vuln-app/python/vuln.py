"""Vulnerable Flask fixture — one planted vuln per reachable CWE family.

RED bed for the shared rule pack. Every route handler below is a real network
entry point (Flask decorator, app.run host=0.0.0.0 → public) so the enumerator
finds it AND the ast-grep rules fire on the sink. Paired safe variants live in
../safe.py. Ground truth: ../MANIFEST.md.

DO NOT run this app. It is intentionally exploitable.
"""

import base64
import os
import pickle
import sqlite3

import requests  # noqa: F401 — third-party SSRF sink
import yaml
from flask import Flask, request, session

app = Flask(__name__)
db = sqlite3.connect(":memory:", check_same_thread=False)

# Fixture-local stand-in for a real ownership store.
ORDERS = {"1": {"owner": "alice", "total": 42}, "2": {"owner": "bob", "total": 99}}


@app.route("/order")
def get_order():
    # CWE-89 SQL Injection — request param interpolated straight into SQL.
    order_id = request.args["id"]
    cur = db.cursor()
    cur.execute(f"SELECT * FROM orders WHERE id = {order_id}")  # VULN:CWE-89
    return str(cur.fetchall())


@app.route("/ping")
def ping():
    # CWE-78 OS Command Injection — request param concatenated into a shell string.
    host = request.args["host"]
    return os.popen("ping -c 1 " + host).read()  # VULN:CWE-78


@app.route("/fetch")
def fetch():
    # CWE-918 SSRF — server fetches an attacker-controlled URL.
    url = request.args["url"]
    return requests.get(url, timeout=5).text  # VULN:CWE-918


@app.route("/download")
def download():
    # CWE-22 Path Traversal — request param used as a filesystem path.
    name = request.args["name"]
    with open("/var/data/" + name) as fh:  # VULN:CWE-22
        return fh.read()


@app.route("/import", methods=["POST"])
def import_blob():
    # CWE-502 Deserialization of untrusted data — pickle over a request body.
    blob = base64.b64decode(request.data)
    obj = pickle.loads(blob)  # VULN:CWE-502
    return str(obj)


@app.route("/config", methods=["POST"])
def load_config():
    # CWE-502 (yaml variant) — yaml.load without SafeLoader on request body.
    return str(yaml.load(request.data))  # VULN:CWE-502-yaml


@app.route("/orders/<order_id>")
def read_order(order_id):
    # CWE-639 IDOR/BOLA — object fetched by id with NO ownership check against session.
    return str(ORDERS[order_id])  # VULN:CWE-639


@app.route("/admin/delete")
def admin_delete():
    # CWE-287 Auth bypass — privileged action with no authentication/authorization gate.
    target = request.args["user"]  # VULN:CWE-287
    return f"deleted {target}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # public bind
