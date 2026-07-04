---
name: agent-teams-quick-start
description: 'Use when planning a multi-perspective pass over the kto-ma-racje app — pre-release audit, security PR review, architecture review, or a multi-file doc/update sweep — and deciding whether to run 2-4 parallel subagents and how to set them up. Also when tempted to enable an "agent teams" mode or env flag.'
---

# Agent Teams Quick Start (kto-ma-racje)

There is **no special "agent teams" mode and no env flag**. Parallel work = **multiple `Agent` tool calls in ONE assistant message** — that alone makes them run concurrently. Separate messages = sequential. You (the parent) block for all, then synthesize.

## Mechanism

- Put all N `Agent` calls in a **single message** → concurrent. This is exactly how `/full-audit` runs its 11 agents — no flag, no CLI setup.
- **Type**: `general-purpose` for open-ended work (audits, reviews, analysis). **Not `Explore`** — it has a smaller prompt budget and overflows ("Prompt too long") on open-ended prompts. See `[[lesson_full_audit_subagent_type_choice]]`.
- **Count**: 2-4, one non-overlapping lens each. Finer slicing just fragments related findings.
- **Read-only in parallel.** The moment an agent might *write* (apply a fix, migration, `git checkout`), two on the same repo stomp each other → give each `isolation: "worktree"` or go sequential. See `[[lesson_parallel_subagent_worktree_race]]`.

## After they return

1. **Grep-verify each claim yourself** before it enters the report — self-report ≠ truth, false positives + occasional hallucinated findings. `[[lesson_subagent_output_verification]]`
2. **One holistic cross-file pass** by you — siloed lenses each pass while an interaction *between* them is broken. `[[lesson_subagent_holistic_final_review]]`
3. For any anti-pattern a lens surfaces, **re-grep the whole repo**, not just touched files. `[[lesson_anti_pattern_repo_sweep]]`

## When to use (decision matrix)

| Use 2-4 parallel agents | Don't — go inline/sequential |
|---|---|
| Pre-release audit, security PR, architecture review | Trivial change (<5 files, 1 domain) |
| Genuinely **non-overlapping** lenses (security / UI-mobile / DB-RLS) | Sequential deps (step B needs step A) |
| High stakes + read-only | Write-heavy on the same files (merge conflicts) |
| Cross-file consistency matters | Tight budget — this is ~3× token cost |

Rule of thumb: worth it when you'd naturally think "I must check X, **and** Y, **and** Z" and those are independent. Otherwise `/pre-deploy-audit` inline.

## Project shortcuts

- **Whole-app pre-release audit** → `/full-audit` (v3: 11 agents, BLOCKER/WARNING/INFO, delta mode). Don't hand-roll it.
- **Scoped diff** → custom 2-4 lens setup; point each lens at its checklist (`vibesec` for security, `/pre-deploy-audit` sub-steps for the rest). Pre-partition overlapping scopes (RLS/edge-fn auth touches both security and DB).

## Common mistakes

- Looking for an env flag / "enable teams" — there isn't one. Just batch `Agent` calls.
- `Explore` for an open-ended audit → shallow / "Prompt too long". Use `general-purpose`.
- Parallel **writers** on one repo → checkout stomp. Worktree-isolate or serialize.
- Shipping subagent findings unverified → grep-check first.
