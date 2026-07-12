// Safe Express fixture — the correct variant of every vuln in vuln.js.
//
// GREEN bed: each rule that FIRES on the matching vuln.js sink must stay SILENT
// here. Same routes, same entry points, sinks sanitized. Ground truth: ../MANIFEST.md.

const express = require("express");
const { execFile } = require("child_process");
const fs = require("fs");
const path = require("path");
const axios = require("axios");

const app = express();
app.use(express.json());
const db = { query: (sql, params, cb) => cb(null, []) }; // stand-in driver

const ACCOUNTS = { 1: { owner: "alice", balance: 42 }, 2: { owner: "bob", balance: 99 } };
const ALLOWED_HOSTS = new Set(["api.internal.example"]);
const DATA_DIR = "/var/data";

app.get("/order", (req, res) => {
  // SAFE CWE-89 — parameterized query, value bound not interpolated.
  db.query("SELECT * FROM orders WHERE id = ?", [req.query.id], (err, rows) => res.json(rows)); // SAFE:CWE-89
});

app.get("/ping", (req, res) => {
  // SAFE CWE-78 — execFile with an argument vector, no shell.
  execFile("ping", ["-c", "1", req.query.host], (err, stdout) => res.send(stdout)); // SAFE:CWE-78
});

app.get("/fetch", (req, res) => {
  // SAFE CWE-918 — host allowlist before the outbound request.
  const host = new URL(req.query.url).hostname;
  if (!ALLOWED_HOSTS.has(host)) return res.status(403).end();
  return axios.get(req.query.url).then((r) => res.send(r.data)); // SAFE:CWE-918
});

app.get("/download", (req, res) => {
  // SAFE CWE-22 — basename strips traversal; join stays under DATA_DIR.
  const name = path.basename(req.query.name);
  fs.readFile(path.join(DATA_DIR, name), "utf8", (err, data) => res.send(data)); // SAFE:CWE-22
});

app.post("/import", (req, res) => {
  // SAFE CWE-502 — JSON.parse builds only plain data, never code.
  const obj = JSON.parse(req.body.data); // SAFE:CWE-502
  res.json(obj);
});

app.get("/accounts/:id", (req, res) => {
  // SAFE CWE-639 — ownership check against the session user before returning.
  const acct = ACCOUNTS[req.params.id];
  if (!acct || acct.owner !== req.session.user) return res.status(404).end();
  return res.json(acct); // SAFE:CWE-639
});

app.listen(8081, "127.0.0.1"); // local bind
