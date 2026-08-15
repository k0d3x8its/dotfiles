#!/usr/bin/env bash
# code-mode persistence hook (UserPromptSubmit).
set -euo pipefail
# Weak models drop method discipline as context grows. Rather than re-injecting an
# anchor every prompt (habituation turns it into wallpaper), emit only when it matters:
#   - the current gate changed since the last emit (transitions are where slips happen)
#   - every 5th turn as a heartbeat (drift sets in ~5-8 turns on smaller models)
#   - GATES.md missing: error state, nag every turn until repaired
# Marker file doubles as state: line 1 = turn count, line 2 = last emitted gate.
# Deactivation = deleting the marker (the skill handles that).
marker="$PWD/.work/.code-active"
[[ -f "$marker" ]] || exit 0

gates_file="$PWD/.work/GATES.md"
if [[ ! -f "$gates_file" ]]; then
	echo "CODE MODE ACTIVE — but .work/GATES.md is missing. Recreate it from the code-mode skill template (Gate 1) before continuing."
	exit 0
fi

count=$(sed -n '1p' "$marker" 2>/dev/null || true)
last_gate=$(sed -n '2p' "$marker" 2>/dev/null || true)
case "$count" in '' | *[!0-9]*) count=0 ;; esac
count=$((count + 1))

gate=$(grep -m1 '^Current gate:' "$gates_file" 2>/dev/null || true)

if [[ "$gate" != "$last_gate" ]] || ((count % 5 == 0)); then
	echo "CODE MODE ACTIVE — ${gate:-gate unknown}. Re-read .work/GATES.md before major moves; update it as gates pass. Deactivate: \"code mode off\"."
	printf '%s\n%s\n' "$count" "$gate" >"$marker"
else
	printf '%s\n%s\n' "$count" "$last_gate" >"$marker"
fi
exit 0
