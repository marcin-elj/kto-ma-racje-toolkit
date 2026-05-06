# kto-ma-racje-toolkit

Personal Claude Code plugin used to develop **[Kto Ma Rację?](https://play.google.com/store)** — a couples-mediation mobile app (React Native + Expo + Supabase). Bundles the skills, hooks and audit workflows I rely on daily.

Most skills are general-purpose (TDD, debugging, lessons-update). One — `full-audit` — is project-specific to "Kto Ma Rację?" and references its schema, edge functions and known anti-patterns. Use it as a template for your own audit skill, or fork it with your project's specifics.

## Skills

| Skill | Scope | What it does |
|---|---|---|
| `full-audit` | project-specific | 10-agent comprehensive audit covering flows, ads, design, i18n, security, subscriptions, integrations, anti-patterns, schema drift, lifecycle/RODO. Reports BLOCKER / WARNING / INFO. |
| `lessons-update` | universal | Reflective pass after fix-phases / multi-file changes — captures anti-patterns, fix-induced regressions, and writes them to `memory/lesson_*.md` for the next session. |
| `tdd-with-claude` | universal | Enforces explicit red-green-refactor (Claude defaults to implementation-first). Anti-patterns + Plan Mode integration. |
| `subagent-driven-development` | universal | Pattern for executing implementation plans through fresh subagents with two-stage review. |
| `agent-teams-quick-start` | universal | Decision matrix for when 2-4 parallel agents are worth the 3x token cost. |
| `search-tools-mastery` | universal | Pick the right search tool: rg vs semantic vs symbol-aware vs AST. Decision tree + combined workflows. |
| `vibesec` | universal | Web/mobile/API security checklist — XSS, CSRF, SQLi, IDOR, secrets, JWT, file upload, SSRF. Server-side validation always. |

## Hooks

### `SessionStart` — `auto-load-lessons-kmr`

Automatically loads operational state and meta-lessons when starting a session inside the kto-ma-racje project tree.

**Selective load** (~3k tokens vs ~12k full):
- `working_memory.md` — current focus + in-flight + recent decisions
- All `feedback_*.md` — process rules
- 4 cross-cutting meta-lessons (audit_self_report, anti_pattern_sweep, schema_drift, gitbash_tooling)

Specific technical lessons (FCM, push tokens, etc.) are NOT auto-loaded — `MEMORY.md` index triggers keyword recognition; lazy-load via Read.

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
2. Edit `skills/full-audit/SKILL.md` — replace project-specific references (Aurora design, edge fn names, schema tables) with yours
3. Edit `hooks/auto-load-lessons-kmr.py` — change the CWD guard string and the `memory_dir` path to match your project
4. Bump `version` in `.claude-plugin/plugin.json`
5. Push and `/plugin install` from your fork

## Adapting `full-audit` to a different stack

`full-audit` is heavily customized for React Native / Expo / Supabase. The 10-agent structure is generic but the checklists embed:
- Aurora design pattern compliance (your design system goes here)
- Supabase edge function consistency checks
- EAS build / Play Console specifics
- React Native i18n + dark mode patterns
- RLS + RODO lifecycle matrix

For a different stack, the 10-agent structure is a useful template but you'll want to rewrite each agent's checklist for your platform.

## License

MIT — see `LICENSE`.

---

Built for personal use; published in case the patterns are useful to others. No support promised.
