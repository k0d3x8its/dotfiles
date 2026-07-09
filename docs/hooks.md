# Hooks

Harness hooks for Claude Code and Codex. Claude has a visible StatusLine event; Codex currently uses backend lifecycle hooks only.

All non-UI hooks suppress stdout by design. Emitting plain stdout can inject text into the model context window and would defeat the zero-token guarantee.

---

## Hook inventory

| Hook file | Agent | Event | What it does |
|-----------|-------|-------|--------------|
| `refresh_triage.py` | Claude, Codex | PostToolUse (Edit/Write) | Auto-refreshes `.memory/TRIAGE-BLOCK.md` when a TODOS.md is edited |
| `session_timer.py` | Claude, Codex | SessionStart / Stop / SessionEnd | Records session start time; emits 45m/55m handoff guidance if the host surfaces hook messages |
| `episodic_index.py` | Codex | SessionEnd | Refreshes the episodic index for projects under `~/dev` |
| `combined-statusline.sh` | Claude only | StatusLine | Renders live cost, burn rate, context %, caveman mode, elapsed time |
| `statusline-bars.sh` | Claude only | (called by combined-statusline) | Computes 5hr/weekly rate-limit burn bar from stdin JSON |

---

## `refresh_triage.py` — Triage auto-refresh

**Event:** PostToolUse on Edit and Write tools.

Path-guards before acting — exits silently if the edited file is not a `TODOS.md` under `~/dev`. When it does match:

1. Derives project name from path (`~/dev/TODOS.md` → `machine`; `~/dev/<proj>/TODOS.md` → `<proj>`)
2. Runs `update-cache <project> <path>` — bumps the mtime pointer in `.triage-cache`
3. Runs `update-triage` — re-renders `.memory/TRIAGE-BLOCK.md` from live content

Silent by design. Any stdout from a PostToolUse hook gets injected back into the model context, which would cost tokens on every edit.

See [triage-system.md](triage-system.md) for the full pipeline.

---

## `session_timer.py` — Session warnings

**Events:** SessionStart, Stop, SessionEnd depending on host.

**SessionStart:** records the current time under the agent home (`~/.claude` or `~/.codex`). Clears one-shot warning markers from the previous session.

**Stop / SessionEnd:** computes elapsed time. At thresholds, emits a JSON `systemMessage` when supported. Claude surfaces this path; Codex hook output visibility is not guaranteed, so Codex must not depend on a visible statusline or banner.

| Threshold | Message |
|-----------|---------|
| 45 minutes | `⚠️ 45m — consider /handoff, /close, or /checkpoint` |
| 55 minutes | `🚨 55m — context getting long` |

The persistent elapsed clock is Claude-only — it updates on every response via `combined-statusline.sh`. Codex does not currently render this statusline surface.

---

## `combined-statusline.sh` + `statusline-bars.sh` — Statusline

**Event:** StatusLine (fires after every response).

`combined-statusline.sh` outputs two lines rendered below each response:

```
🤖 Sonnet 4.6 | 💰 $0.12 session / $0.84 today | 🔥 $0.08/hr | 🧠 18k (9%)
[CAVEMAN full] ⏱  23m   5h ▮▮▮▯▯▯▯▯▯▯ 30%  ·  wk ▮▮▮▮▮▯▯▯▯▯ 52%
```

**Line 1** (`ccusage statusline`): model name, session cost, daily cost, burn rate, context tokens + %.

**Line 2** (bottom row, left to right):
- Caveman badge — read from `~/.claude/.caveman-active`; blank when off
- Session elapsed timer — flips to `⚠️ 45m` at 45 min, `🚨 55m` at 55 min with `/handoff` nudge
- 5h + weekly API rate-limit burn bars — sourced from `rate_limits.five_hour.used_percentage` and `rate_limits.seven_day.used_percentage` in the StatusLine stdin JSON (server-authoritative, no local reconstruction)

`statusline-bars.sh` renders each bar as a 10-tick block (`▮` filled, `▯` empty) with a numeric %. Color bands: green <50%, yellow 50–80%, orange 80–90%, red ≥90%. Missing rate limit data shows dimmed empty ticks + `--%` rather than a fabricated 0%.
