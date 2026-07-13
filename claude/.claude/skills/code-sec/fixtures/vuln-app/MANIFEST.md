# vuln-app — Fixture Ground Truth

Shared `/tdd` red-green bed for the bounty-hunter / code-sec deterministic core.
Tests and future domain packs read THIS file — never hardcode fixture facts.
Every planted vuln is a real network entry point so the entry-point enumerator
finds it AND the tiered ast-grep rule pack fires on the sink; each has a paired
SAFE variant the rule must stay SILENT on.

**Do not run these apps — they are intentionally exploitable.**

Reachable CWE families: SQLi, OS command injection, SSRF, path traversal,
deserialization, IDOR/BOLA, auth bypass, buffer overflow (embedded C/C++).

## Entry points (for the enumerator)

Each app binds public (`0.0.0.0`) in its `vuln.*` and local (`127.0.0.1`) in its
`safe.*`, so the enumerator's exposure-guess column has both cases to classify.

| File | Routes | Bind | Exposure guess |
|---|---|---|---|
| `python/vuln.py` | 8 | `0.0.0.0:8080` | public |
| `python/safe.py` | 7 | `127.0.0.1:8081` | local |
| `node/vuln.js` | 6 | `0.0.0.0:8080` | public |
| `node/safe.js` | 6 | `127.0.0.1:8081` | local |
| `arduino/vuln.ino` | 2 | WiFi AP `:80` | public |
| `arduino/safe.ino` | 2 | WiFi AP `:80` | public |

**Total enumerable entry points across the fixture: 31.**
Per-file counts are the stable assertion targets (route list below); the total
is derived and will move if routes are added — assert per file, not the sum.
Arduino binds public in BOTH variants (a WiFi device is inherently networked;
the safe/vuln split is the sink fix, not the bind) — the local-bind exposure case
is already covered by `python/safe.py` and `node/safe.js`.

Route inventory (path → handler line):
- `python/vuln.py`: `/order`@27 `/ping`@36 `/fetch`@43 `/download`@50 `/import`@58 `/config`@66 `/orders/<order_id>`@72 `/admin/delete`@78
- `python/safe.py`: `/order`@26 `/ping`@35 `/fetch`@45 `/download`@54 `/config`@62 `/orders/<order_id>`@68 `/admin/delete`@77
- `node/vuln.js`: `/order`@22 `/ping`@28 `/fetch`@33 `/download`@38 `/import`@43 `/accounts/:id`@49
- `node/safe.js`: `/order`@20 `/ping`@25 `/fetch`@30 `/download`@37 `/import`@43 `/accounts/:id`@49
- `arduino/vuln.ino`: `/read`@33 `/greet`@34   (listener: `WebServer server(80)`@14)
- `arduino/safe.ino`: `/read`@30 `/greet`@31   (listener: `WebServer server(80)`@10)

## Planted vulns → CWE → sink line → safe variant

`Reachable` = remote-reachable subset bounty-hunter selects. `Auth tier`:
`unauth` (unauthenticated-external), `any-user` (authenticated-any-user, the
IDOR/BOLA tier), `priv` (privilege-escalation target).

### Python (Flask)

| CWE | Family | Vuln sink | Safe variant | Reachable | Auth tier |
|---|---|---|---|---|---|
| CWE-89  | SQL injection        | `python/vuln.py:32` (f-string) | `python/safe.py:31` (parameterized `?`) | yes | unauth |
| CWE-78  | OS command injection | `python/vuln.py:40` (`os.popen` + concat) | `python/safe.py:41` (`subprocess.run` argv) | yes | unauth |
| CWE-918 | SSRF                 | `python/vuln.py:47` (`requests.get(url)`) | `python/safe.py:51` (host allowlist) | yes | unauth |
| CWE-22  | Path traversal       | `python/vuln.py:54` (`open("/var/data/"+name)`) | `python/safe.py:58` (`basename`+`join`) | yes | unauth |
| CWE-502 | Deserialization (pickle) | `python/vuln.py:62` (`pickle.loads`) | none by design — avoid pickle; see JSON/`safe_load` | yes | unauth |
| CWE-502 | Deserialization (yaml)   | `python/vuln.py:69` (`yaml.load`) | `python/safe.py:65` (`yaml.safe_load`) | yes | unauth |
| CWE-639 | IDOR / BOLA          | `python/vuln.py:75` (no owner check) | `python/safe.py:74` (owner==session user) | yes | any-user |
| CWE-287 | Auth bypass          | `python/vuln.py:81` (no auth gate) | `python/safe.py:77`–`82` (role gate) | yes | priv |

### Node (Express)

| CWE | Family | Vuln sink | Safe variant | Reachable | Auth tier |
|---|---|---|---|---|---|
| CWE-89  | SQL injection        | `node/vuln.js:24` (string concat) | `node/safe.js:22` (bound `?` param) | yes | unauth |
| CWE-78  | OS command injection | `node/vuln.js:30` (`exec` + concat) | `node/safe.js:27` (`execFile` argv) | yes | unauth |
| CWE-918 | SSRF                 | `node/vuln.js:35` (`axios.get(url)`) | `node/safe.js:34` (host allowlist) | yes | unauth |
| CWE-22  | Path traversal       | `node/vuln.js:40` (`readFile("/var/data/"+name)`) | `node/safe.js:40` (`basename`+`join`) | yes | unauth |
| CWE-502 | Deserialization      | `node/vuln.js:45` (`node-serialize` `unserialize`) | `node/safe.js:45` (`JSON.parse`) | yes | unauth |
| CWE-639 | IDOR / BOLA          | `node/vuln.js:51` (no owner check) | `node/safe.js:53` (owner==session user) | yes | any-user |

### Arduino / ESP (C/C++)

Embedded web-server sinks — the device's WiFi server is the network entry point.
ast-grep parses `.ino` via its C++ grammar (auto-detected). CWE-120 is the
embedded-specific family; path traversal reuses CWE-22.

| CWE | Family | Vuln sink | Safe variant | Reachable | Auth tier |
|---|---|---|---|---|---|
| CWE-22  | Path traversal   | `arduino/vuln.ino:19` (`SPIFFS.open("/data/"+name)`) | `arduino/safe.ino:16` (allowlist → fixed path, no concat) | yes | unauth |
| CWE-120 | Buffer overflow  | `arduino/vuln.ino:27` (`strcpy` unbounded) | `arduino/safe.ino:24` (`snprintf` bounded) | yes | unauth |

## Notes for rule authors (see deepsec `writing-matchers.md`)

- Match the SHAPE, not fixture identifiers — a SQLi rule keys on
  "request value reaches SQL string by interpolation/concat", not the literal
  `order_id`/`req.query.id` names. Both language pairs above are deliberately
  minimal so a rule that keys on names would pass the test yet miss real code.
- Deserialization has no universal safe pair: `pickle.loads` and
  `node-serialize.unserialize` are dangerous by construction, so those rules
  fire whenever the call is present. The GREEN check for the deser rules is the
  ABSENCE of the dangerous call in the safe file (the safe variant uses
  `yaml.safe_load` / `JSON.parse`), not a neutered call on the same line.
- Auth-bypass (CWE-287) and IDOR (CWE-639) are reachability/authorization
  judgments, not pure sink patterns — the rule pack flags the candidate
  (privileged route with no guard / object fetch by id with no owner check);
  the model's reachability gate confirms the tier. Expect these two to live in
  the `noisy`/`normal` tiers, the injection sinks in `precise`.
