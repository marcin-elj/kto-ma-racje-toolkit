# kto-ma-racje-toolkit

Personal Claude Code plugin used to develop **[Kto Ma Rację?](https://play.google.com/store)** — a couples-mediation mobile app (React Native + Expo + Supabase). Bundles the skills, hooks and audit workflows I rely on daily.

All skills here are general-purpose (TDD, debugging, lessons-update). The project-specific ones live in the app repo itself, under `.claude/skills/` — including `full-audit`, which moved there in v0.7.0 because it references that repo's schema, scripts and CI gates, and is versioned alongside them.

## Skills

| Skill | Scope | What it does |
|---|---|---|
| `lessons-update` | universal | Reflective pass after fix-phases / multi-file changes — captures anti-patterns, fix-induced regressions, and writes them to `memory/lesson_*.md` for the next session. |
| `tdd-with-claude` | universal | Enforces explicit red-green-refactor (Claude defaults to implementation-first). Anti-patterns + Plan Mode integration. |
| `subagent-driven-development` | universal | Pattern for executing implementation plans through fresh subagents with two-stage review. |
| `agent-teams-quick-start` | universal | Decision matrix for when 2-4 parallel agents are worth the 3x token cost. |
| `search-tools-mastery` | universal | Pick the right search tool: rg vs semantic vs symbol-aware vs AST. Decision tree + combined workflows. |
| `vibesec` | universal | Web/mobile/API security checklist — XSS, CSRF, SQLi, IDOR, secrets, JWT, file upload, SSRF. Server-side validation always. |

## Hooks

### `SessionStart` — `auto-load-lessons-kmr`

A **router**, not a content dump. Contract `karta-v1` (v0.6.0):

- **karta** — fixed-size pointers: where operational state lives, the newest session-block heading (extracted from the file, never hand-copied), the mandatory `recall.py` rule, and „don't guess live versions".
- **`feedback_*`** — one indicator line each (name + category + truncated `description`), not the rule text.
- **HOTLIST** — same shape, for nodes with `krytyczna: true`, collected data-driven from front-matter.

**`working_memory.md` is NOT loaded** — only pointed at. It is ~41k characters and the harness drops any `additionalContext` above a **measured** threshold of (9 600, 9 999] **characters** into a file, feeding the model a ~2 KB preview (a list of filenames). Until v0.5.0 this hook composed 47 979 characters and exited 0, delivering nothing for ~198 sessions. Everything that grows now goes through `python memory/recall.py <nouns>` or Read.

**Budget is enforced, and trimming is loud.** The hook measures its own output against `BUDZET_ZNAKI = 9200`; if the corpus outgrows it, HOTLIST survives before process rules (irreversible beats recoverable) and the output says explicitly how many items were dropped and how to recover them. Regression tests: `tests/test_autoload_budget.py` (run in CI).

`AUTOLOAD-KONTRAKT: <name>` is printed in the output so the contract can be **verified from outside** instead of assumed.

**CWD guard**: only fires when session cwd contains `kto-ma-racje`. If you fork this for another project, edit the guard in `hooks/auto-load-lessons-kmr.py`.

## Install

```bash
# add this marketplace
/plugin marketplace add marcin-elj/kto-ma-racje-toolkit

# install the plugin
/plugin install kto-ma-racje-toolkit@marcin-elj
```

Or directly from the repo:

```bash
/plugin install kto-ma-racje-toolkit@github:marcin-elj/kto-ma-racje-toolkit
```

## Forking for your own project

1. Fork this repo
2. Edit `hooks/auto-load-lessons-kmr.py` — change the CWD guard string and the `memory_dir` path to match your project
3. Bump `version` in **both** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — `claude plugin update` reads the marketplace one, so a stale version there is a silent no-op
4. Push and `/plugin install` from your fork

## License

MIT — see `LICENSE`.

---

Built for personal use; published in case the patterns are useful to others. No support promised.
