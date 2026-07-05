#!/usr/bin/env python
"""SessionStart hook for the "Kto Ma Rację?" project.

Selective load: process meta-lessons + feedback rules + working memory.
Specific technical lessons (FCM, push tokens, expo-file-system, deep links,
dead buttons, etc.) are NOT auto-loaded — MEMORY.md index triggers
recognition by keyword; full content read lazily via Read tool when match.

Token cost: ~3k (vs ~12k full load).

CWD guard: only fires when session cwd is inside kto-ma-racje project tree.

Memory location (v0.1.2 change):
1. Prefer REPO memory at <repo>/memory/ — walk up from CWD looking for
   memory/MEMORY.md. This is the canonical, versioned location since
   PR #146 in kto-ma-racje repo. Works on any fresh clone / new machine
   immediately after `git pull` — no per-machine sync needed.
2. Fall back to GLOBAL per-machine cache at
   ~/.claude/projects/D--Projects-kto-ma-racje/memory/ if no repo memory
   found (covers branches that don't have memory/ yet, or sessions
   running outside the worktree).
"""

import json
import os
import sys
import glob


def find_repo_memory(start: str, max_levels: int = 12) -> str | None:
    """Walk up from `start` looking for a `memory/MEMORY.md` file.

    Returns the absolute `memory/` directory path if found within
    `max_levels` ancestors, else None. Guards against infinite loops
    by counting levels and stopping at filesystem root.

    Why MEMORY.md specifically: any project might have a `memory/`
    folder for unrelated reasons. The presence of MEMORY.md (our
    index file) is a strong signal that this is the kmr memory dir.
    """
    cur = os.path.abspath(start)
    for _ in range(max_levels):
        candidate = os.path.join(cur, "memory")
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "MEMORY.md")
        ):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:  # filesystem root
            return None
        cur = parent
    return None


def _fm_fields(path: str):
    """Zwraca (krytyczna: bool, kategoria: str, summary: str) z front-mattera.

    Minimalny, self-contained parser (hook nie importuje recall.py z repo).
    summary = description (RECONCILE) LUB skrot. Brak front-mattera => nie-krytyczna.
    """
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False, "", ""
    if not text.startswith("---"):
        return False, "", ""
    end = text.find("\n---", 3)
    header = text[3:end] if end != -1 else text[3:]
    kry, kat, desc, skrot = False, "", "", ""
    for line in header.splitlines():
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k == "krytyczna" and v.lower() == "true":
            kry = True
        elif k == "kategoria":
            kat = v
        elif k == "description":
            desc = v
        elif k == "skrot":
            skrot = v
    return kry, kat, (desc or skrot)


def main() -> None:
    # CWD guard
    cwd = os.getcwd().replace("\\", "/").lower()
    if "kto-ma-racje" not in cwd:
        sys.exit(0)

    # Prefer repo-versioned memory (canonical since PR #146 in kto-ma-racje).
    # Walk up from CWD looking for memory/MEMORY.md.
    memory_dir = find_repo_memory(os.getcwd())
    source = "repo"

    if memory_dir is None:
        # Fall back to global per-machine cache (legacy behavior).
        memory_dir = os.path.join(
            os.path.expanduser("~"),
            ".claude",
            "projects",
            "D--Projects-kto-ma-racje",
            "memory",
        )
        source = "global-cache"

    if not os.path.isdir(memory_dir):
        sys.exit(0)

    files: list[str] = []

    # 1. Operational state
    working = os.path.join(memory_dir, "working_memory.md")
    if os.path.isfile(working):
        files.append(working)

    # 2. All feedback_*.md (process rules)
    files.extend(sorted(glob.glob(os.path.join(memory_dir, "feedback_*.md"))))

    # 3. HOTLIST — lekcje krytyczna:true zbierane DATA-DRIVEN (flaga na wezle,
    # zero hardcoded nazw). Zastepuje statyczna liste meta-lekcji, ktora cicho
    # gnila: referencja do przemianowanego lesson_audit_self_report_distrust
    # ladowala 3 z 4. Ladujemy SUMMARY (nie pelna tresc) — lean reminder net;
    # pelna tresc on-demand przez memory/recall.py / Read (filozofia map/router).
    hotlist: list[str] = []
    for pat in ("lesson_*.md", "project_*.md", "reference_*.md", "checklist_*.md"):
        for path in sorted(glob.glob(os.path.join(memory_dir, pat))):
            kry, kat, summ = _fm_fields(path)
            if kry:
                hotlist.append(
                    "- %s [%s] — %s"
                    % (os.path.basename(path)[:-3], kat or "?", summ))

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

    if not parts and not hotlist:
        sys.exit(0)

    if hotlist:
        parts.append(
            "===== HOTLIST (krytyczna:true — nieodwracalne/kosztowne, ZAWSZE w "
            "glowie; pelna tresc: `python memory/recall.py <slowa>` lub Read) =====\n"
            + "\n".join(hotlist))

    intro = (
        f"Auto-loaded for kto-ma-racje session (source: {source}).\n\n"
        "STRUCTURE:\n"
        "1. working_memory.md = current operational state (focus, in-flight, "
        "decisions). Edit directly without confirm.\n"
        "2. feedback_*.md = process rules. Apply proactively.\n"
        "3. HOTLIST = lekcje krytyczna:true (data-driven z front-mattera) — "
        "nieodwracalne/kosztowne patterny (security / RLS / RODO / gate / "
        "verify-jwt / external-verify / data-loss). SUMMARY tylko.\n\n"
        "Pozostale lekcje NIE sa auto-loadowane — odkrywalne przez "
        "`python memory/recall.py <rzeczowniki>` (hook UserPromptSubmit podrzuca "
        "kandydatow z promptu) albo MEMORY.md; czytaj pelny plik przez Read gdy "
        "trafienie pasuje do biezacego zadania.\n\n"
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
