#!/usr/bin/env bash
# SessionStart hook for "Kto Ma Rację?" project.
# Plugin-aware wrapper — Python implementation lives in companion .py file
# inside this plugin's hooks/ directory, NOT in ~/.claude/hooks/.
#
# Why python:
#   - jq missing from standard Git Bash on Windows
#   - embedding python -c '...' broke on Polish apostrophes
#
# CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is installed.
# Falls back to script-relative resolution for direct invocation in tests.
set -e
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
exec python "${PLUGIN_ROOT}/hooks/auto-load-lessons-kmr.py"
