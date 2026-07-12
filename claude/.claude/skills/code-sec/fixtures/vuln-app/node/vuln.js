// Vulnerable Express fixture — one planted vuln per reachable CWE family.
//
// RED bed for the shared rule pack. Every handler is a real network entry
// point (Express route, listen on 0.0.0.0 → public) so the enumerator
// finds it AND the ast-grep rules fire on the sink. Paired safe variants live
// in ./safe.js. Ground truth: ../MANIFEST.md.
//
// DO NOT run this app. It is intentionally exploitable.

const express = require("express");
const { exec } = require("child_process");
const fs = require("fs");
const axios = require("axios");
const { unserialize } = require("node-serialize");

const app = express();
app.use(express.json());
const db = { query: (sql, cb) => cb(null, []) }; // stand-in driver

const ACCOUNTS = { 1: { owner: "alice", balance: 42 }, 2: { owner: "bob", balance: 99 } };

app.get("/order", (req, res) => {
  // CWE-89 SQL Injection — request param concatenated into the query string.
  const q = "SELECT * FROM orders WHERE id = " + req.query.id; // VULN:CWE-89
  db.query(q, (err, rows) => res.json(rows));
});

app.get("/ping", (req, res) => {
  // CWE-78 OS Command Injection — request param interpolated into a shell command.
  exec("ping -c 1 " + req.query.host, (err, stdout) => res.send(stdout)); // VULN:CWE-78
});

app.get("/fetch", (req, res) => {
  // CWE-918 SSRF — server fetches an attacker-controlled URL.
  axios.get(req.query.url).then((r) => res.send(r.data)); // VULN:CWE-918
});

app.get("/download", (req, res) => {
  // CWE-22 Path Traversal — request param used directly as a filesystem path.
  fs.readFile("/var/data/" + req.query.name, "utf8", (err, data) => res.send(data)); // VULN:CWE-22
});

app.post("/import", (req, res) => {
  // CWE-502 Deserialization of untrusted data — node-serialize on a request body.
  const obj = unserialize(req.body.data); // VULN:CWE-502
  res.json(obj);
});

app.get("/accounts/:id", (req, res) => {
  // CWE-639 IDOR/BOLA — object fetched by id with NO ownership check.
  res.json(ACCOUNTS[req.params.id]); // VULN:CWE-639
});

app.listen(8080, "0.0.0.0"); // public bind
