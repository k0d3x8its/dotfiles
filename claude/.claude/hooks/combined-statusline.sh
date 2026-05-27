#!/bin/bash
# Pipe Claude Code's stdin (session JSON) to ccusage, then show caveman mode below
INPUT=$(cat)
echo "$INPUT" | ccusage statusline 2>/dev/null || true
bash "$HOME/.claude/hooks/caveman-statusline.sh"
