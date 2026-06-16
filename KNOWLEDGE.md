# dotfiles Knowledge

> Curated facts about this codebase. Promoted via /checkpoint or /remember.
> Committed with the repo — not a session file.

---

- Verify command: `shellcheck install.sh && bats --tap tests/ && python3 -m unittest discover -s tests -p "test_*.py" -v` (mirrors .github/workflows/ci.yml; read by /trust-but-verify detect.md priority 1)
- CI (ci.yml) triggers only on push to main and PRs to main — feature-branch pushes never run CI; local verify command is the only pre-merge gate.
- Triage rendering deliberately lives in `scripts/update-triage` (python) + `refresh_triage.py` hook, not in the model — reverses an earlier design (bash-inline `decide()`, no persisted snapshot). Persisting `TRIAGE-BLOCK.md` is fine because a PostToolUse hook regenerates it at zero model tokens (kills the "rebuild costs tokens" objection); python over bash for testability (82 tests, CI-gated). `/dev-brief triage` is demoted to cache-repair only. Don't re-propose bash-inline or no-snapshot.

