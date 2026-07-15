---
name: lessons-update
description: Wspólna nauka — po każdym fix-phase / multi-file change / non-trivial task przejrzyj sesję i zdecyduj czy warto zapisać lekcję (nową lub update istniejącej). Triggeruj proaktywnie po PR-ach, fazach audytu, zamknięciu commit'u, każdej okazji gdy coś poszło nie tak / fix wprowadził nowy bug / wykryłem powtarzający się pattern. Skip dla trivial reads, pure refactors bez błędów, doc updates. Auto-save bez pytania (od 2026-07-04); po zapisie pokaż zwięźle co zapisane.
---

# Lessons Update — wspólny skill nauki

Cel: po każdym non-trivial task wyciągnąć to czego się nauczyliśmy i zachować jako persistent memory, żeby kolejne sesje nie powtarzały tych samych błędów. Memory ładuje się przez SessionStart hook (project-scoped), więc każda zapisana lekcja zwiększa baseline competence wszystkich przyszłych sesji.

## Kiedy uruchamiać

**Triggery proaktywne** (sam to wywołaj, nie czekaj):
- Po `gh pr merge` / commit zakończonym
- Po fazie audytu (Faza 1/3/4/5/...)
- Po multi-file change (≥3 pliki) lub multi-step task
- Po wykryciu fix-induced regression (najgorszy signal — fix wprowadził nowy bug)
- Po backtracking (musiałeś cofnąć decyzję)
- Po surprise (kod zachowywał się inaczej niż zakładałeś)

**Skip rules**:
- Trivial reads (sprawdzanie statusu, ls, grep do informacji)
- Pure refactors bez napotkania błędów
- Documentation updates
- Akcje które tylko klikają w UI / ustawiają flagi
- Powtarzanie znanego procesu bez nowych wniosków

**Jawny trigger od usera**: `/lessons-update` lub "zaktualizuj lessons" / "co się nauczyliśmy?".

## Workflow

### Krok 1: Recap

Streszcz w 1-3 zdaniach co właśnie zostało zrobione. To context dla decyzji "warto / nie warto".

### Krok 2: Reflection — 5 pytań

Przejdź po sesji i odpowiedz uczciwie. Każde "tak" = kandydat na lesson:

1. **Czy coś się nie udało lub zaskoczyło?** (TS error po commit, edge case który zignorowałem, fail w MCP call)
2. **Czy musiałem backtrack'ować lub fix'ować fix?** ⚠️ **Najwyższy signal** — fix-induced regressions.
3. **Czy coś założyłem co się okazało nieprawdą?** (np. "bonus_analyses jest w migracjach", "invokeEdge zwraca FunctionsHttpError shape")
4. **Czy widzę pattern który może się powtórzyć?** (np. "subagent zaraportował clean ale nie sprawdził callerów")
5. **Co bym chciał wiedzieć upfront następnym razem?**

### Krok 3: Detect duplicates

Dla każdego kandydata, **najpierw sprawdź czy już istnieje lesson** w `memory/`:

```bash
# Cwd guard — wykryj projekt
PROJ_MEM="$HOME/.claude/projects/$(pwd | sed 's|/|-|g' | sed 's|^-||')/memory"
# fallback: kto-ma-racje
[ -d "$PROJ_MEM" ] || PROJ_MEM="$HOME/.claude/projects/D--Projects-kto-ma-racje/memory"

# Search by keyword from candidate
grep -li "<keyword>" "$PROJ_MEM"/lesson_*.md
```

Jeśli istnieje pasująca lekcja:
- **Update path** (krok 5) — append nowy case do istniejącej
- NIE twórz duplikatu

Jeśli nie istnieje:
- **Create path** (krok 4) — nowa lekcja

### Krok 4: Create new lesson

**Filename convention**: `lesson_<short_topic>.md` (lub `feedback_*` jeśli to feedback procesowy, nie technical anti-pattern).

**Template** (front-matter grafu OBOWIĄZKOWY od Plan 3 — gate `memory-brain`/lint
w `pr-checks.yml` FAILuje lekcję bez `kategoria`/niepustych `tagi`/summary):

```markdown
---
name: <short title>
description: <keyword-rich summary — TO jest summary recall (recall.py reużywa description); słowa którymi impuls faktycznie pada, PL+EN, ~1 zdanie>
type: lesson | feedback
kategoria: <jedna z memory/_categories.txt: process-discipline | auth-session | ui-rn-runtime | push | analytics | db-rls | ads-monetization | iap-pricing | build-eas-store | tooling-devenv | project-decision | reference-infra | release-checklist | marketing | pricing | integrations>
tagi: [<słowa-triggery którymi ktoś SZUKA tej lekcji — PL+EN, np. rls, delete, supabase, rodo>]
krytyczna: <true TYLKO gdy nieodwracalne/kosztowne (security/RLS/RODO/gate/verify-jwt/external-verify/data-loss) → trafia do hotlistu always-load; inaczej false>
powiazane: [<opcjonalnie lesson_x bez .md; rośnie on-touch>]
---

**Reguła**: <jednozdaniowa zasada do zapamiętania>

**Why**:
<konkretny case z sesji — co się stało, dlaczego, jaki był koszt (wasted hours, regresja, security gap, RODO leak). MUSI być specyficzny: file:line, error message, exact symptom. Bez "uważaj na bugi".>

**How to apply**:
- <konkretny check do wykonania w przyszłości — bullet point>
- <grep / pattern / file path do sprawdzania>
- Related: `[[lesson_x]]` — **linkuj wikilinkami**; lekcje żyją w grafie Obsidiana przez junction `kmr-memory/`, więc `[[...]]` wiąże je w mózgu (a `[[nieistniejące]]` = TODO na przyszłą lekcję, nie błąd)

**Occurrences**:
- <data> — <session ID jeśli masz, inaczej krótki opis>: <co się stało>
```

> **Strażnik odkrywalności (spec §11): NOWA lekcja = NOWY case.** Dopisz parę
> `impuls → [lesson_slug]` do `memory/tests/recall_cases.yaml` i sprawdź, że
> `python memory/tests/recall_score.py` nadal PASS (lekcja jest w top-5 dla swojego
> impulsu). Jeśli miss → dopracuj `tagi`/`description`. To gate `memory-brain` (krok 5).
>
> **`skrot` tylko fallback:** gdy z jakiegoś powodu nie ma `description`, użyj `skrot: "..."` (≤200 znaków). Preferuj `description` (reconcile — jedno pole = summary + trigger).

### Krok 5: Update existing lesson

Jeśli pattern się powtórzył — **NAJPIERW zbumpuj licznik we front-matterze** (P1,
2026-07-15: zliczanie w polach, nie w prozie — proza nie jest grep-owalna dla
automatów, licznik jest):

```yaml
wystapienia: 2            # bump o 1 (jeśli pola nie ma — dodaj z wartością 2:
                          #  oryginalny case + ten nawrót)
ostatnie: RRRR-MM-DD      # data DZISIEJSZEGO nawrotu
automat: <mechanizm>      # OBOWIĄZKOWE przy wystapienia>=2 (gate lint_frontmatter
                          #  failuje bez tego pola). Wpisz istniejący mechanizm
                          #  ("gate X (plik, testy)") albo jawnie "brak (<plan>)"
```

Potem dopisz **nowy occurrence** do prozy (narracja zostaje — licznik jej nie zastępuje):

```markdown
**Occurrences**:
- 2026-04-25 — original case: <opis>
- 2026-05-02 — <new case>: <co się stało, czemu pattern się powtórzył mimo lekcji>
```

> Dług (wystapienia>=2 + automat "brak…") raportuje `python scripts/report_automation_debt.py`
> — konsumowany przez tygodniową konsolidację i poniedziałkową meta-naukę.

Plus jeśli reflection ujawnia **nową fasetę patternu** której wcześniej nie było:
- Dopisz do **How to apply** nowy bullet
- Update **Reguła** jeśli się rozjeżdża (rzadko — większość patternów jest stała)

**⚠️ Automat > lekcja (OBOWIĄZKOWE gdy occurrence ≥2)**: jeśli po dopisaniu tej
lekcja ma **≥2 wystąpienia**, NIE kończ na dopisku „occurrence". Zaproponuj
mechanizm czyniący nawrót niemożliwym: check w `pr-checks.yml` (wzorce:
`tier-grep`, `anti-pattern-lint`, `migration-lint`, `memory-index-size`), hook,
DB constraint, config w repo, krok skilla. Dowód (meta-audyt 2026-07-03): nawracały
WYŁĄCZNIE reguły pamięciowe; frykcje domknięte automatem nie wróciły ani razu.
Jeśli pattern jest grep-owalny — automat już od 1. wystąpienia. Poniedziałkowa
meta-nauka konsumuje occurrence-count właśnie po to.

### Krok 6: Auto-save + pokaż po zapisie (decyzja Marcina 2026-07-04)

**Zapisuj BEZ pytania o zgodę** — jak auto-capture mózgu dowodzenia (Second
Brain). Lekcje trafiają do grafu Obsidiana automatycznie (junction
`kmr-memory/`), więc mózg uczy się z automatu.

Po zapisie pokaż userowi ZWIĘŹLE co zapisałeś (tytuł + reguła w 1 zdaniu per
lekcja), żeby mógł zawetować:

```
Zapisane lekcje:
- [nowa] lesson_X — <reguła 1 zdanie>
- [update] lesson_Y — occurrence: <co doszło>
(cofnij/zmień: powiedz którą)
```

_(Historyczne: do 2026-07-04 obowiązywał ALWAYS-CONFIRM gate — zniesiony
jawną decyzją Marcina w sesji 2026-07-04.)_

### Krok 7: MEMORY.md map-guard (NIE dodawaj linii indeksu)

> **Po cutoverze Fazy 3 (2026-07-05) `MEMORY.md` to MAPA/router, NIE płaski indeks.**
> Nowa lekcja NIE dostaje linii w `MEMORY.md` — odkrywalność zapewnia front-matter
> grafu (Krok 4: `kategoria`/`tagi`/`krytyczna`) + case w `recall_cases.yaml` +
> `recall.py`. To domyka klasę „append-only indeks → sufit ~24 KB".

**Czego NIE robić:** nie czytaj mapy po to, by dopisać `- [<title>](<file>.md) — …`.
Kuszące „pomogę i zaktualizuję indeks" wskrzesza płaski spis → mapa puchnie z powrotem.

**Co zrobić:**
1. `MEMORY.md` ruszasz **TYLKO** gdy lekcja wprowadza całą NOWĄ `kategoria`
   (rzadko) — wtedy dodaj wiersz do tabeli kategorii w mapie + wpis do
   `memory/_categories.txt`.
2. W innym wypadku mapy **nie dotykasz**.
3. Map-guard: `MEMORY.md` musi zostać **≤ 8192 B** (gate CI `memory-index-size` w
   `.github/workflows/pr-checks.yml`, ODWRÓCONY 2026-07-05 na map-stays-a-map:
   FAIL > 8192 B, WARN > 6144 B). Jeśli mapa przebija limit → wraca płaski spis:
   usuń dopisane linie lekcji (detale należą do plików lekcji + `recall.py`).

### Krok 8: Confirm save + close

Po zapisie potwierdź userowi:
```
✅ Saved: <path>
Discoverable via: front-matter (kategoria/tagi) + recall_cases.yaml + recall.py (bez linii w MEMORY.md)
Active in next session via SessionStart hook pluginu (`${CLAUDE_PLUGIN_ROOT}/hooks/auto-load-lessons-kmr.cmd`) + UserPromptSubmit recall hook; w sesjach remote-control (cloud, gdzie `.cmd` nie odpala) — przez `/session-start`.
```

## Heuristyki jakości lekcji

**DOBRA lekcja**:
- Specyficzna: file:line, error code, exact pattern
- Trigger-friendly: keyword w opisie który ja zobaczę w przyszłym kodzie
- Actionable: "How to apply" ma checks/greps/triggers, nie ogólne rady
- Bounded: jedna lekcja = jeden pattern (nie kombo 3 niezwiązanych)

**ZŁA lekcja** (nie zapisuj):
- "Uważaj na bugi" / "Pisz dobre testy"
- Restating dokumentacji frameworka (znajdę w docs)
- Trivia o jednym pliku które nie powtarza się (use comment in code, not memory)
- Duplikaty istniejących lekcji bez nowego signal

## Self-check przed wywołaniem

Zanim invoke'uję ten skill, zadaj sobie:
- Czy jest cokolwiek z 5 pytań reflection do zachowania? Jeśli **wszystkie nie** → skip skill, NIE wywołuj.
- Jeśli jest 1+ kandydat → invoke i przejdź workflow.

## Integracja z innymi skillami

- **`full-audit` v2**: na końcu każdej fazy audytu (Faza 1/3/4/5/...) explicit wskazuje "now invoke lessons-update". Dodaj sentence do report sekcji "PLAN NAPRAWY" w full-audit.
- **`anthropic-skills:consolidate-memory`**: po cutoverze 2026-07-05 `MEMORY.md` to mapa ~4 KB (map-guard FAIL > 8192 B) — nie rośnie z liczbą lekcji, więc rutynowa konsolidacja indeksu odpada. Consolidate-memory zostaje narzędziem do sprzątania KORPUSU (dedupe/merge lekcji), nie mapy.
- **`session-summary`**: na koniec sesji może wywołać lessons-update jako ostatni step.

## Auto-detect project

Hook ładuje lessons na podstawie cwd. Ten skill MUSI zapisywać do tego samego folderu memory:

```bash
# Detect project memory dir
CWD_LOWER=$(pwd | tr '[:upper:]' '[:lower:]')
case "$CWD_LOWER" in
  *kto-ma-racje*) PROJ_MEM="$HOME/.claude/projects/D--Projects-kto-ma-racje/memory" ;;
  *) PROJ_MEM="$HOME/.claude/projects/$(pwd | sed -e 's|^/c|C-|' -e 's|/|-|g' -e 's|^-||' -e 's|^C--|D--|')/memory" ;;
esac
```

Dla nowych projektów: jeśli memory dir nie istnieje, `mkdir -p` plus utworzenie pustego MEMORY.md indexu.

## Output do user (final summary)

Po skończonym workflow, podsumuj:
```
Lessons review:
- Reflected on N kandydatów
- Saved: M nowych / K updated existing
- Skipped: J (reasons listed)

MEMORY.md: <KB>KB (mapa/router; map-guard limit 8 KB — nietknięta chyba że nowa kategoria)

Co poszło najlepiej w tej sesji: <jedna fraza>
Co najbardziej kosztowało: <jedna fraza>
```

To zamyka pętlę nauki — user widzi jakie lekcje wpadły do długoterminowej pamięci.
