---
name: code-sec
description: Project security sweep — gitleaks full-history secret scan, dependency audit (auto-detect npm/pip/cargo/go), git-crypt coverage check against the File Taxonomy, and input-handling greps. Findings become tagged [SECURITY] TODOs. Use for /code-sec, "security sweep", "audit this project for security", or when the [SECURITY] TODO tag routes here. For reviewing a specific diff/PR use ce-security-reviewer; for plan-level review use ce-security-lens-reviewer.
---

# code-sec — Project Security Sweep

Full-project security audit. Output is a findings list routed into `TODOS.md`
as tagged `[SECURITY]` items — never silent fixes. Drop caveman mode for the
report: security findings must be unambiguous.

## Ground rules

- **Read-only sweep.** Never fix, rotate, or delete during the audit. Findings → TODOs; remediation is its own task.
- **Never print a discovered secret.** Reference file:line + rule ID only. Use `--redact` on every gitleaks call.
- **Severity-tag every finding**: `[BROKEN]` (live leaked secret in a public repo), `[BLOCKER]` (secret in history / unencrypted sensitive file about to be pushed), default (hardening gap), `[LOW]` (defense-in-depth).

## Sweep phases (run all, in order)

### 1. Secret scan — full history

```bash
gitleaks git --redact --no-banner --exit-code 1   # full history, run from repo root
gitleaks dir . --redact --no-banner --exit-code 1  # working tree incl. untracked
```

Exit 1 = findings. For each: file, rule ID, commit (history hits). A secret in
HISTORY needs rotation + possibly purge — flag it `[BLOCKER][DECISION]` (purge
is a rewrite; user decides — see dotfiles §1.5 precedent where purge was
declined for non-secret PII).

### 2. Dependency audit — auto-detect the stack

| Marker file | Command |
|---|---|
| `package.json` | `npm audit --audit-level=moderate` (or `pnpm audit`/`yarn audit` per lockfile) |
| `requirements*.txt` / `pyproject.toml` | `pip-audit` if installed, else `osv-scanner -r .` if installed, else note "no Python auditor installed" as a `[LOW]` finding |
| `Cargo.toml` | `cargo audit` (if installed) |
| `go.mod` | `govulncheck ./...` (if installed) |

Report vulnerable package → advisory ID → fixed version. Do NOT auto-upgrade.

### 3. git-crypt coverage vs File Taxonomy

Files that hold session narrative / plans / knowledge MUST be encrypted on any
repo with a remote (CLAUDE.md File Taxonomy): `KNOWLEDGE.md`, `TODOS.md`,
`.memory/SESSION-LOG.md`, `.work/PLAN.md`, `.work/FINDINGS.md`,
`.work/PROGRESS.md`, `docs/GDD-*.md`, `docs/PRD-*.md`, `docs/ARD-*.md`,
`docs/post-mortems/*` (public repos).

```bash
git-crypt status -e 2>/dev/null            # what IS encrypted
git ls-files | grep -E 'KNOWLEDGE|TODOS|SESSION-LOG|\.work/|GDD-|PRD-|ARD-'  # what EXISTS tracked
```

- Tracked taxonomy file NOT in `git-crypt status -e` → finding (severity `[BLOCKER]` if the repo has a public remote, default otherwise).
- No git-crypt at all but taxonomy files tracked → route to `/encrypt`.
- Check `.gitattributes` patterns are **root-anchored** (`/KNOWLEDGE.md` not `KNOWLEDGE.md`) — unanchored patterns encrypt nested template copies.
- Verify an encrypted file's staged blob actually starts `\0GITCRYPT` before trusting the attribute.

### 4. Input-handling scan — ast-grep first, rg for the rest

**Structural patterns via ast-grep** (matches real call/assignment nodes, so
comments, docstrings, and string fixtures don't false-positive — near-zero
eyeball overhead vs grep):

```bash
# Python — dynamic execution & shell injection
ast-grep -p 'eval($X)' -l py .
ast-grep -p 'exec($X)' -l py .
ast-grep -p 'os.system($X)' -l py .
ast-grep -p 'subprocess.$FN($$$ARGS, shell=True)' -l py .
# Python — unsafe deserialization
ast-grep -p 'pickle.loads($$$)' -l py .
ast-grep -p 'yaml.load($$$)' -l py .        # then confirm no SafeLoader arg
ast-grep -p 'marshal.loads($$$)' -l py .
# JS/TS — dynamic execution & DOM injection
ast-grep -p 'eval($X)' -l js .   # repeat with -l ts
ast-grep -p 'new Function($$$)' -l js .
ast-grep -p 'execSync($$$)' -l js .
ast-grep -p '$EL.innerHTML = $X' -l js .
ast-grep -p 'dangerouslySetInnerHTML' -l tsx . 2>/dev/null || rg -n 'dangerouslySetInnerHTML'
# Lua (nvim configs/plugins) — dynamic execution
ast-grep -p 'loadstring($X)' -l lua .
ast-grep -p 'load($X)' -l lua .
ast-grep -p 'os.execute($X)' -l lua .
ast-grep -p 'io.popen($X)' -l lua .
```

For complex constraints (e.g. `yaml.load` WITHOUT SafeLoader), write a YAML
rule with a `not:` clause — see the `ast-grep` skill for rule syntax.

**Textual patterns via rg** (string/byte-level targets an AST can't express, or
languages ast-grep has no grammar for — shell, config files):

```bash
# credentials in code/config — string literals across ANY file type
rg -in 'password\s*=\s*["'\'']|api_?key\s*=\s*["'\'']|token\s*=\s*["'\'']|secret\s*=\s*["'\'']' -g '!*.lock'
# world-writable / permissive (shell scripts, Makefiles)
rg -n 'chmod\s+(-R\s+)?0?77[67]|umask\s+0+'
# pipe-to-shell in scripts/docs (install instructions count — they get copy-pasted)
rg -n '(curl|wget)[^|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b'
```

ast-grep hits are near-conclusive; rg hits are candidates — eyeball rg hits in
context before they become findings.

### 5. App-layer pass (only when the repo serves HTTP / exposes endpoints)

Skip for pure CLIs, configs, and libraries with no request surface.

- **Input points** — map every place external data enters (`req.body/params/query`, Flask `request.*`, form handlers, WebSocket messages). Each one needs validation: type, length, format. Unvalidated input feeding phases-4 sinks is a `[BLOCKER]`.
- **SQL injection** — any string concatenation/f-string/interpolation building a query is a finding, even if "the input is trusted today"; parameterized queries only. `ast-grep -p 'cursor.execute($SQL % $$$)' -l py` and f-string variants; eyeball ORM `.raw()`/`text()` calls.
- **XSS / output escaping** — every point user content is rendered: template auto-escape not disabled (`| safe`, `{% autoescape off %}`, `v-html`), innerHTML sinks already in phase 4, CSP header present on served pages.
- **Auth/authz** — every endpoint states its auth requirement explicitly; authorization checked at BOTH route and resource level (object ownership, not just "logged in"); look for privilege-escalation paths (IDs from client trusted, mass-assignment of role fields, unsafe redirects after login).

Close-out checklist for this phase (all verified or N/A-with-reason):

- [ ] All inputs validated and sanitized
- [ ] SQL queries parameterized (no string building)
- [ ] Output escaping on all user content + CSP where pages are served
- [ ] Auth on every endpoint; authz at resource level
- [ ] CSRF protection on state-changing routes
- [ ] HTTPS enforced; security headers configured
- [ ] Error messages / logs leak no sensitive data

### 6. Harness surface (only when auditing a repo that ships Claude Code config)

For repos containing `.claude/`, hooks, or skills (e.g. dotfiles): check hooks
for exfiltration paths (network calls, transcript reads sent anywhere),
settings for `enableAllProjectMcpServers`/`ANTHROPIC_BASE_URL` overrides, and
skills for hidden-unicode (`rg -n '[​-‏ -‮]'`).

## Output

1. **Findings report** in the session (grouped by phase, severity-first). Each finding: what, where (file:line / commit), why it matters, suggested remediation.
2. **Append to `TODOS.md`** — one tagged item per actionable finding, `[SECURITY]` + severity + phase context. Confirm with the user before writing.
3. If zero findings in a phase, say so explicitly — silence is not a clean bill.

## Close-out

- Never mark the sweep "done" without having RUN phases 1–4 fresh (trust-but-verify: read the exit codes).
- Offer follow-ups: `/encrypt` for coverage gaps, `/diagnose` for any confirmed vuln, rotation checklist for leaked secrets.
