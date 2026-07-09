---
name: harness-audit
description: Audit the Codex harness's OWN attack surface — hooks, skills-as-supply-chain, plugins, MCP servers, settings overrides, memory injection points, CVE version floor. Use for /harness-audit, "audit my Codex setup", "check my hooks/plugins for anything malicious", or after installing a new plugin/marketplace/MCP server. Distinct from /code-sec (audits a PROJECT repo); this audits the harness that runs Codex itself. For a per-repo slice (a repo that ships .codex/), /code-sec phase 6 points here.
---

# harness-audit — Codex Surface Audit

The harness is a privileged execution environment: hooks run arbitrary code on
every session and tool call, skills and plugins inject third-party instructions
into context, settings can redirect the model or widen auto-approval. This
skill audits that surface. Drop caveman mode for the report: security findings
must be unambiguous.

## Ground rules

- **Read-only.** Findings → tagged `[SECURITY]` TODOs in `dotfiles/TODOS.md` (the harness is dotfiles-managed); remediation is its own task.
- **Never print a discovered secret or exfil URL payload** — file:line + description only.
- Apply `/code-sec`'s Finding discipline verbatim: taint-trace, CONFIRMED/TRACED/CANDIDATE tiers, suppress-list. A hook that COULD exfiltrate but demonstrably doesn't (trace its data flow) is a CANDIDATE at most.
- Severity: `[BROKEN]` (active exfiltration / model redirect found), `[BLOCKER]` (auto-approval wide open, unpinned supply chain executing code), default (hardening gap), `[LOW]` (defense-in-depth).

## Threat model (why each phase exists)

| Surface | Threat |
|---|---|
| Hooks | Arbitrary code, every session/tool-call — highest privilege. Exfil of transcripts (they contain everything you've typed + file contents), env harvesting |
| Skills/plugins | Prompt-injection supply chain: third-party instructions loaded into context; hidden-unicode payloads invisible in review |
| MCP servers | Tool supply chain with network reach; auto-approval multiplies it |
| settings.json | `ANTHROPIC_BASE_URL` redirects the model itself; permissive allow-lists silently widen the blast radius of everything above |
| Memory / AGENTS.md | Persistent instruction injection — one poisoned line executes every session forever |
| Transcripts on disk | Secrets sink: anything a tool ever printed lives in `~/.codex/projects/*/` plaintext |

## Audit phases (run all, in order)

### 1. Surface inventory

Enumerate before scanning — new-since-last-audit items get FIRST attention:

```bash
python3 -c "import json;d=json.load(open('$HOME/.codex/settings.json'));print(json.dumps(d.get('hooks',{}),indent=1))"
ls ~/.codex/hooks/ ~/dev/dotfiles/claude/.codex/hooks/ 2>/dev/null
ls ~/.codex/skills/          # note which are symlinks (dotfiles-managed) vs loose
cat ~/.codex/plugins/installed_plugins.json
ls ~/.mcp.json ./.mcp.json 2>/dev/null; python3 -c "import json;d=json.load(open('$HOME/.codex/settings.json'));print(d.get('enabledPlugins'),d.get('extraKnownMarketplaces'))"
```

Findings here: hook registered in settings but file missing (dangling exec),
hook file present but NOT registered (dead code or staged payload), loose
skill in `~/.codex/skills/` that is not a dotfiles symlink (unmanaged =
unreviewed), plugin/marketplace you don't recognize.

### 2. Hook audit — the highest-privilege surface

Every registered hook file, plus anything in a hooks dir:

```bash
# network egress — any of these in a hook is a finding until traced benign
rg -n 'curl|wget|nc |ncat|socat|fetch\(|urllib|requests\.|http\.client|XMLHttpRequest' ~/dev/dotfiles/claude/.codex/hooks/ ~/.codex/hooks/ 2>/dev/null
# transcript/exfil pairing — reading the transcript is normal for timers; reading it AND having network reach is not
rg -ln 'transcript_path' ~/dev/dotfiles/claude/.codex/hooks/ 2>/dev/null
# obfuscation in a hook = hostile until proven otherwise
rg -n 'base64|eval\(|exec\(|compile\(|__import__|marshal|pickle' ~/dev/dotfiles/claude/.codex/hooks/ ~/.codex/hooks/ 2>/dev/null
# writes outside expected state dirs (state files, /tmp, project .work/.memory are expected)
rg -n 'open\([^)]*[\"'\''](/(?!tmp)|~)' ~/dev/dotfiles/claude/.codex/hooks/ 2>/dev/null
```

Per hit: taint-trace. A `requests.` import in a hook that only writes local
state = CANDIDATE; transcript read + network call in the SAME hook = file at
`[BROKEN]` and read every line of that file. Expected self-hits: the guard
hooks CONTAIN the strings they block (command_guard's own regexes mention
curl/wget) — pattern-in-a-regex-literal is not egress (field-test 2026-07-07). Also judge fail-direction per
hook: guards (secret_guard, command_guard) fail-OPEN by design (documented);
anything failing open that GRANTS (auto-approve helpers) is a finding.

### 3. Skill / plugin supply chain

```bash
# hidden unicode — ESCAPED class (a literal class would plant invisible chars
# in this very file and self-hit every audit; same gotcha as code-sec phase 6)
rg -n '[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2066}-\x{2069}]' ~/.codex/skills/ ~/.codex/plugins/cache/ 2>/dev/null
# instructions steering the MODEL toward egress or approval-widening
rg -in 'curl .*\| *(ba|z)?sh|--dangerously|settings\.local|enableAllProjectMcpServers|ANTHROPIC_BASE_URL' ~/.codex/plugins/cache/ 2>/dev/null
```

Third-party plugin skills load their name+description into EVERY session and
their body on invoke — treat each installed plugin as a standing dependency.
Check versions pinned in `installed_plugins.json` vs marketplace cache drift.
Unused plugins are pure surface: flag any not invoked in recent memory as
`[LOW]` removal candidates (context cost is a bonus argument, see the
plugin-bloat TODO).

### 4. Settings audit

```bash
python3 - <<'EOF'
import json, os
for p in (os.path.expanduser("~/.codex/settings.json"), ".codex/settings.json", ".codex/settings.local.json"):
    if os.path.exists(p):
        d = json.load(open(p))
        print(p, "→ env:", d.get("env"), "| apiKeyHelper:", d.get("apiKeyHelper"),
              "| allProjectMcp:", d.get("enableAllProjectMcpServers"),
              "| allow:", len(d.get("permissions",{}).get("allow",[])),
              "| deny:", d.get("permissions",{}).get("deny"))
EOF
```

- `ANTHROPIC_BASE_URL` / `apiKeyHelper` set → `[BROKEN]` unless you set it deliberately (proxy) — this redirects the model or leaks the key.
- `enableAllProjectMcpServers: true` → `[BLOCKER]` (any cloned repo's `.mcp.json` auto-runs).
- Allow-list: eyeball every `Bash(...)` glob for over-broad grants (`Bash(*)`, `Bash(rm *)`); deny-list absent → default finding.
- Project `.codex/settings.local.json` in OTHER repos can carry all of the above — sweep `~/dev/*/.codex/settings*.json` too.

### 5. MCP servers

For each server in any `.mcp.json` / plugin config: transport (stdio binary =
who ships it; http = where does it point), and whether its tools are on the
allow-list. No MCP configured = say so and move on.

### 6. Version floor (CVE check)

```bash
claude --version   # floor: ≥1.0.111 and ≥2.0.65 (known-CVE fixes); stale = [BLOCKER]
```

Query live advisories if the version is old — never recite CVE numbers from
memory (hallucination risk); `gh api` / web search for "claude code CVE".

### 7. Memory & instruction files

```bash
rg -n '[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2066}-\x{2069}]' ~/.codex/AGENTS.md ~/.codex/KNOWLEDGE.md ~/.codex/projects/*/memory/ 2>/dev/null
rg -in 'curl|wget|base64|ANTHROPIC' ~/.codex/projects/*/memory/*.md 2>/dev/null
```

These files are trusted instructions executed every session — a poisoned
memory line is persistent compromise. Any hit gets read in full context.

## Output

1. **Minimum Bar Checklist** (all verified or finding-linked):
   - [ ] Every registered hook read + traced: no untraced network egress, no transcript-read+egress pairing, no obfuscated exec
   - [ ] No hidden unicode in skills, plugin cache, or memory files
   - [ ] No `ANTHROPIC_BASE_URL`/`apiKeyHelper` surprise; `enableAllProjectMcpServers` false/absent
   - [ ] Allow-list globs individually justified; deny-list present
   - [ ] Every plugin/marketplace recognized + version-pinned; unused ones flagged for removal
   - [ ] MCP servers enumerated with transport + reach stated (or none)
   - [ ] `claude --version` at or above CVE floor
2. **Findings** → `dotfiles/TODOS.md` as `[SECURITY]`-tagged items (confirm before writing). Zero findings in a phase = say so explicitly.
3. Offer follow-ups: `/code-sec` on dotfiles itself, plugin uninstall for flagged surface.

## Close-out

- Trust-but-verify: every scan above RUN fresh this audit — read exit codes; piped scanners need `${PIPESTATUS[0]}`.
- The trailing explicit paths on every `rg` are load-bearing (bare rg reads stdin and hangs in non-tty shells — field-test 2026-07-07).
- Record the audit date; next audit prioritizes what changed since (`git -C ~/dev/dotfiles log --since=<date> -- claude/` + plugin-cache mtimes).
