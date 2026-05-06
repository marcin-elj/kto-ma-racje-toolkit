@echo off
REM Windows wrapper for auto-load-lessons-kmr SessionStart hook.
REM Forwards to the Python implementation in this plugin's hooks/ directory.
REM CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is installed.
python "%CLAUDE_PLUGIN_ROOT%\hooks\auto-load-lessons-kmr.py"
