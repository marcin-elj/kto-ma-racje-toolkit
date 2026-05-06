#!/usr/bin/env python
"""SessionStart hook for the "Kto Ma Rację?" project.

Selective load: process meta-lessons + feedback rules + working memory.
Specific technical lessons (FCM, push tokens, expo-file-system, deep links,
dead buttons, etc.) are NOT auto-loaded — MEMORY.md index triggers
recognition by keyword; full content read lazily via Read tool when match.

Token cost: ~3k (vs ~12k full load).

CWD guard: only fires when session cwd is inside kto-ma-racje project tree.
"""

import json
import os
import sys
import glob


def main() -> None:
    # CWD guard
    cwd = os.getcwd().replace("\\", "/").lower()
    if "kto-ma-racje" not in cwd:
        sys.exit(0)

    memory_dir = os.path.join(
        os.path.expanduser("~"),
        ".claude",
        "projects",
        "D--Projects-kto-ma-racje",
        "memory",
    )
    if not os.path.isdir(memory_dir):
        sys.exit(0)

    files: list[str] = []

    # 1. Operational state
    working = os.path.join(memory_dir, "working_memory.md")
    if os.path.isfile(working):
        files.append(working)

    # 2. All feedback_*.md (process rules)
    files.extend(sorted(glob.glob(os.path.join(memory_dir, "feedback_*.md"))))

    # 3. Meta-lessons — cross-cutting anti-patterns that apply to ANY task.
    # Specific technical lessons load lazily via Read.
    meta_names = [
        "lesson_audit_self_report_distrust.md",
        "lesson_anti_pattern_repo_sweep.md",
        "lesson_schema_drift_check.md",
        "lesson_gitbash_windows_tooling.md",
    ]
    for name in meta_names:
        path = os.path.join(memory_dir, name)
        if os.path.isfile(path):
            files.append(path)

    # Dedup preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)

    if not unique:
        sys.exit(0)

    parts: list[str] = []
    for path in unique:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            parts.append(f"===== {os.path.basename(path)} =====\n{content}")
        except Exception:
            continue

    if not parts:
        sys.exit(0)

    intro = (
        "Auto-loaded for kto-ma-racje session.\n\n"
        "STRUCTURE:\n"
        "1. working_memory.md = current operational state (focus, in-flight, "
        "decisions). Edit directly without confirm.\n"
        "2. feedback_*.md = process rules. Apply proactively.\n"
        "3. meta-lessons (audit_self_report, anti_pattern_sweep, schema_drift, "
        "gitbash_tooling) = cross-cutting anti-patterns. Apply to ANY task.\n\n"
        "Specific technical lessons (FCM, push tokens, expo-file-system, claude "
        "model aliases, deep link routes, dead buttons, debug_logs, dev gates, "
        "EAS build, i18next, Android linking, Play Console, push token format, "
        "credentials gitignore) are NOT loaded. MEMORY.md index triggers "
        "recognition by keyword; read the file via the Read tool when a match "
        "appears in the current task.\n\n"
    )

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": intro + "\n\n".join(parts),
        }
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
