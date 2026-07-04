---
name: search-tools-mastery
description: 'Use when about to search the kto-ma-racje codebase and picking how — an exact/known string vs a fuzzy concept whose names you do not know, a safe cross-file rename, or a repeating anti-pattern you keep hand-grepping. Also when tempted to reach for a semantic/AST/symbol search tool.'
---

# Search Tools Mastery (kto-ma-racje)

Match search **intent** to the tool that is **actually installed here**. The model already knows "use rg for exact text" — the value below is the non-obvious project layer: which real tool per intent, what is NOT installed, and the subagent gotchas.

## Intent → real tool

| Intent | Tool | Note |
|---|---|---|
| Known/exact string, symbol, import | **Grep** (ripgrep) | `.rpc('name')` call sites, `import ... from`, error strings |
| File by path / name / glob | **Glob** | `**/*.tsx`, `supabase/functions/**` |
| Concept / "where does X happen", names unknown | **`Explore` subagent** | `very thorough` when the answer likely spans multiple files/naming conventions, else `medium`; returns the conclusion |
| Structural (all async fns, all imports, multi-line) | **Grep** with regex / `multiline: true` | escape literal braces; no AST tool here |
| Safe cross-file **rename** | **Grep** to enumerate def + call sites + string refs → edit → **re-grep for 0 remaining** | never blind `sed`; verify zero |
| Repeating anti-pattern | **don't hand-grep every session** → add a check to `pr-checks.yml` | see `[[lesson_anti_pattern_repo_sweep]]` |

**Scope a Grep** with `glob:` / `path:` / `type:` to search a known string inside a subtree — e.g. `glob: "supabase/functions/**"` or `type: "ts"`. That's one Grep call, not Grep + a separate Glob.

## NOT installed here — don't invoke

`grepai`, `Serena`, `ast-grep`, and any semantic/embedding search are **not** in this environment (verify against `memory/reference_integrations.md`). Do not call them — that's hallucination. For "search by meaning" the real substitute is an **`Explore` subagent**. New MCP search tooling installs at the **end** of a session (loads only after restart).

## Subagent gotchas (the real value)

- **`Explore` locates, it doesn't audit.** It reads excerpts and has a smaller prompt budget → open-ended audits/reviews overflow it ("Prompt too long"). For open-ended work use **`general-purpose`**. See `[[lesson_full_audit_subagent_type_choice]]`.
- **Verify findings externally.** A subagent's self-report ≠ truth — re-run the grep/command yourself before acting on it. See `[[lesson_subagent_output_verification]]`.
- **Sweep the whole repo, then automate.** A known anti-pattern recurs by nature: grep the entire repo (not just the file in front of you), fix all, then encode a CI check so it can't come back. See `[[lesson_anti_pattern_repo_sweep]]`.

## Common mistakes

- Semantic/`Explore` for a **known** symbol name → slow, indirect. Known string = **Grep**, first try.
- **Grep** for a fuzzy concept (`auth.*login.*session`) → misses variations. Unknown names = **`Explore`**.
- Blind `sed`/replace-all rename without re-grepping for 0 remaining → orphaned call sites.
