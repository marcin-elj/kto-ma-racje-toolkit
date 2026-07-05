---
name: full-audit
description: 'Kompletny, wielowymiarowy audyt aplikacji "Kto Ma Rację?". Uruchom gdy user poprosi o "pełny audyt", "full audit" lub "audyt aplikacji". Uruchamia 11 agentów równolegle i dostarcza zbiorczy raport BLOCKER/WARNING/INFO. Wersja v3 (2026-07-04) — dodane: decisions ledger z mózgu (vault+memory), derive-dont-hardcode, obowiązkowa weryfikacja findingów, agent Analytics & observability, tryb delta, wynik audytu do vaulta.'
---

Przeprowadź KOMPLETNY, WIELOWYMIAROWY audyt aplikacji "Kto Ma Rację?".

## Filozofia audytu (post-retrospective 2026-05-01)

**Subagent self-reports = false positives.** "TS clean + verified" w raporcie subagenta nie znaczy "działa". Wymagaj konkretów: paste tsc output, paste grep callerów, simulate path mentally.

**Anti-patterns powtarzają się.** Gdy znajdujesz instance znanego anti-patternu (z `lesson_*.md`), sweep CAŁY repo grep'em — nie tylko obecne miejsce.

**Fixy wprowadzają nowe bugi.** Każdy fix-phase wymaga osobnego re-audytu zmienionych ścieżek. Zwłaszcza: contract changes (return shapes), routing additions (mutability of destination), nowe screens (visual pattern compliance).

**Schema drift jest realny.** Live DB ≠ migrations folder. Cross-check `information_schema.tables` vs `supabase/migrations/` periodycznie.

**RODO per-lifecycle, nie tylko delete-account.** Cross-partner PII access matrix per event: signup / pair-create / dispute / pair-unpair / partner-deleted / account-delete. Każdy event ma inny cleanup contract.

**Świadome decyzje ≠ bugi (v3).** Część „nieprawidłowości" to jawne decyzje Marcina (np. email confirm OFF od 2026-05-15, Google Ads zawieszone = zero akwizycji Android, brak definicji eventu w PostHogu przy śladowym wolumenie). Bez decisions ledger audytor produkuje fałszywe BLOCKERY. Ledger budujesz w pre-audit i WSTRZYKUJESZ każdemu agentowi.

**Derive, don't hardcode (v3).** Liczby i listy (capy tierów, lista fns AI, model subskrypcji, wersje) wyprowadzaj z żywych źródeł w momencie audytu (`lib/tier.ts`, grep po funkcjach, `memory/tech_state.md`) — stałe zaszyte w tym skillu gniją między wydaniami (lesson_automation_prompt_names_drift; w v2 zgniły capy, liczba fns AI i model subskrypcji).

---

## Pre-audit checklist

Zanim zaczniesz — przeczytaj:
1. `CLAUDE.md` — zasady projektu, znane pułapki, historia
2. `docs/PUBLICATION-CHECKLIST.md` — co było sprawdzane wcześniej
3. Ostatnie podsumowania sesji z `docs/session-summaries/`
4. `supabase/migrations/` — wszystkie migracje DB po kolei
5. `lib/translations/pl.ts` i `en.ts` — kompletność tłumaczeń + delta od ostatniego audytu
6. Pamięć (`memory/lesson_*.md`, `memory/feedback_*.md`) — znane anti-patterns do sweep'u
7. Ostatnie 5 commitów w git log — zrozum co się ostatnio zmieniło

### Decisions ledger — mózg przed dispatchem (v3, OBOWIĄZKOWE)

Zbuduj listę „świadome stany — NIE flagować jako bug" i wklej ją do promptu KAŻDEGO agenta:
1. `memory/project_*.md` — wszystkie (aktywne decyzje: email confirm OFF, zawieszone Google Ads, pricing tiers, social login status…)
2. Vault (mózg Jarvisa, `D:\SecondBrain`): huby `projekty/kto-ma-racje.md`, `projekty/kmr-growth.md`, `projekty/google-ads-zawieszenie.md`, `projekty/apple-search-ads.md` + sekcja Decyzje w `warsztat/second-brain.md`
3. Najnowszy digest `D:\SecondBrain\projekty\kmr-digesty\` (lub rollup tygodniowy) — bieżące anomalie już ZNANE (nie odkrywaj ich ponownie jako findings)
4. Format ledgera: `- <stan> — decyzja/kontekst (źródło) — NIE flagować`

### Żywe źródła prawdy (v3 — derive, don't hardcode)

Przed dispatchem wyprowadź i wklej agentom:
- **Capy tierów**: przeczytaj `lib/tier.ts` + `supabase/functions/_shared/tier-limits.ts` (flaguj rozjazd między nimi — to jest finding; NIE porównuj z liczbami z tego skilla)
- **Lista fns AI**: `grep -l "anthropic" supabase/functions/*/index.ts` — WSZYSTKIE znalezione porównujesz w Agent 5 (2026-07: było ich 7, nie 4)
- **Model subskrypcji**: `memory/tech_state.md` (2026-07: hybryda per-user — `profiles.subscription_*` + RPC `effective_tier_for_user` max-of-pair)
- **Stan CI**: `gh run list --limit 5` — jeśli pr-checks czerwone, to finding sam w sobie

### Recall lekcji (mózg) — przed dispatchem (Plan 3, wzmocnienie (c))

Zamiast czytać wszystkie `lesson_*.md` (checklist pkt 6), odpal impuls na obszary audytu i **wstrzyknij trafienia do promptów agentów** (jak decisions ledger):
```bash
python memory/recall.py rls delete edge deploy verify jwt      # Agent DB/RLS
python memory/recall.py auth session signin race spinner       # Agent auth/session
python memory/recall.py push notification analytics posthog    # Agent analytics
python memory/recall.py build eas vc testflight altool         # Agent build/release
# …jeden impuls per wymiar audytu
```
Dla obszarów security / RLS / RODO / deploy recall jest **OBOWIĄZKOWY**. Lekcje `krytyczna:true` są już w hotliście (auto-load przez SessionStart hook) — recall domyka resztę. Wypisz jawnie, co podniósł, i przekaż odpowiednim agentom.

Uruchom **11 agentów równolegle**, każdy na innym obszarze. Zbierz wszystkie wyniki i dostarcz jeden zbiorczy raport z priorytetami BLOCKER / WARNING / INFO.

### Tryb delta (opcjonalny)

Gdy user poda punkt odniesienia („audyt od ostatniego audytu / od daty X / od taga"), agenci 1-7 i 11 priorytetyzują pliki z `git log --since=<X> --name-only` (pełna głębia tylko na diffie), a pełne repo-wide sweepy zostają wyłącznie w Agentach 8-10. Bez parametru = pełny audyt.

## ⚠️ Subagent type — KRYTYCZNE

**WSZYSTKIE 11 agentów MUSI używać `subagent_type: "general-purpose"`.** NIE używaj `Explore` dla żadnego.

Powód (lesson 2026-05-17): full-audit dispatched 10 agentów, 7/10 padło natychmiast z "Prompt is too long" — wszystkie 7 miały `Explore`, wszystkie 3 które przeszły miały `general-purpose`. `Explore` ma mniejszy input prompt budget bo jego system prompt jest bogatszy (search strategies, breadth modes). Audyt = open-ended cross-cutting analysis = dokładnie ten case dla którego tool description literalnie mówi "Do NOT use Explore for code review, design-doc auditing, cross-file consistency checks, or open-ended analysis".

Jeśli mimo `general-purpose` któryś agent padnie z "Prompt is too long" — skróć tylko jego prompt, nie wszystkich. Patrz `memory/lesson_full_audit_subagent_type_choice.md`.

---

## AGENT 1: FLOW UŻYTKOWNIKA — END-TO-END

Przetestuj każdą możliwą ścieżkę użytkownika od początku do końca. Dla każdej ścieżki sprawdź: czy każdy krok ma następny krok, czy żaden ekran nie jest ślepy zaułek, czy wszystkie dane przechodzą między krokami.

### Ścieżki do zbadania:

**Rejestracja i onboarding:**
- Nowy user → rejestracja emailem → email confirmation → pierwszy ekran
- Co się dzieje jeśli user nie potwierdzi emaila i spróbuje się zalogować?
- Co się dzieje jeśli user kliknie link potwierdzający po wygaśnięciu?
- Onboarding slides → czy można je pominąć? → co się dzieje po ostatnim?
- Czy profil usera jest tworzony automatycznie przy signup? (trigger v7)

**Parowanie partnerów:**
- Osoba A generuje kod → Osoba B wpisuje kod → para połączona
- Gdzie dokładnie Osoba B wpisuje kod? Czy jest to oczywiste w UI?
- Co się dzieje jeśli kod wygaśnie?
- Co się dzieje jeśli dwie osoby wpisują ten sam kod jednocześnie? (race condition)
- Co się dzieje jeśli Osoba B jest już w innej parze?
- Co się dzieje jeśli Osoba A usunie konto zanim B dołączy?
- Czy deep link `ktomaracje://join/CODE` (legacy) i `ktomaracje://pair?code=X&token=Y` (Aurora) otwierają właściwy ekran?

**Flow sporu — pełna ścieżka:**
- Osoba A tworzy spór → wpisuje temat → wpisuje swój tekst → wysyła
- Osoba B dostaje powiadomienie push → otwiera apkę → widzi TYLKO temat (nie tekst A)
- Osoba B wpisuje swoją wersję → wysyła
- Oboje widzą ekran oczekiwania na zgodę → oboje klikają "Zgadzam się"
- REVEAL: oboje widzą oba teksty jednocześnie (Supabase Realtime)
- AI analiza się ładuje → werdykt się wyświetla w kartach (VerdictCard)
- Kontynuacja sporu → czy rate limit jest sprawdzany? czy state się resetuje (votes/reflections/emotions)?

**Edge cases w flow sporu:**
- Co jeśli Osoba A zamknie apkę w trakcie czekania na B?
- Co jeśli B nie odpowie przez 24h?
- Co jeśli internet padnie podczas analizy AI? (sprawdź AbortController timeout + self-heal)
- Co jeśli AI zwróci błąd 502/503? (sprawdź czy `analysis_failed` UI faktycznie się pokazuje — verify error.message/code propagation przez `invokeEdge`)
- Co jeśli jeden partner odmówi "Zgadzam się" przy reveal?
- Co jeśli partner usunie konto w trakcie aktywnego sporu?

**Solo / Trening (v3 — od 1.2.0):**
- Mapa scenariuszy → szczegóły → sesja czatu (`app/solo/[sessionId].tsx`) → debrief z gwiazdkami → tablica postępów
- „Kontynuuj rozmowę" przy aktywnej sesji (porzucenie NIE pali slotu — verify)
- Cap sesji per tier (pill X/Y w headerze) + rewarded-ad bonus (`grant_solo_bonus` RPC) + flow po wyczerpaniu limitu
- Interstitial na exit z debriefu — czy nie strzela w środku flow?

**Social login (v3 — od 1.2.0):**
- Google Sign-In i Apple Sign-In: happy path → profil utworzony → routing jak email signup
- Anulowanie w połowie OAuth → czy user nie ląduje w limbo?
- Konto email istnieje + logowanie social tym samym adresem → co się dzieje?

**Win-back / referral (v3):**
- Deep link `/win-back` i `/referral` → screen istnieje, suppression w `isInterruptSuppressedRoute`, pricing z RC (nie hardcoded)
- `redeem_referral_code` RPC — happy + błędne kody

**Logowanie i sesja:**
- Login emailem + hasłem → przekierowanie na właściwy ekran
- Co się dzieje po wygaśnięciu sesji Supabase?
- Czy token refresh działa w tle?
- Password reset flow — od emaila do zmiany hasła. Po `updateUser({password})` czy pozostałe sesje są invalidowane (`signOut({scope: "others"})`)?

**Usuwanie konta vs unpair (RODO):**
- User wchodzi w Profil → Usuń konto → type-to-confirm → usuń. Czy `delete-account` czyści WSZYSTKIE tabele (profiles, couples, disputes, notifications, push_tokens, emotional_profiles, debug_logs, bonus_analyses)?
- Pair-unpair (consensual): czy `emotional_profiles` są DELETE'owane (bo couples archive ≠ couples delete, FK cascade nie strzela)?
- Czy partner dostaje powiadomienie?

### State machine completeness (NOWE):
- **Enumeracja**: dla każdej entity (dispute, couple, profile) wylistuj WSZYSTKIE możliwe statusy
- **UI coverage**: czy każdy status ma branch w UI list views (np. dashboard list)? Czy stuck states (`analyzing`, `both_done`) mają visual cue?
- **Routing destination mutability** (NOWE): gdy nowa ścieżka prowadzi do screen X, sprawdź czy user na archived/disabled couple może wykonać write actions których nie powinien

### Silent return audit (NOWE — repo-wide sweep):
- Grep `if (!user) return;` w onPress/onSubmit handlers → każdy musi mieć Alert
- Grep `await supabase.from(...).update(...).eq(...)` BEZ `.then(({error})=>...)` lub `const { error } =` przed → silent failure risk
- Grep `await supabase.from(...).insert(...)` ten sam wzorzec
- Lista wszystkich znalezionych: file:line, dla każdego oceń czy fail będzie visible userowi

---

## AGENT 2: REKLAMY — STRATEGIA, IMPLEMENTACJA, EFEKTYWNOŚĆ

### Audyt techniczny:
- Gdzie dokładnie jest wywoływany interstitial? Znajdź KAŻDE wywołanie w kodzie
- Gdzie jest wywoływany banner? rewarded? app-open?
- Czy AdMob SDK jest poprawnie zainicjalizowany przy starcie apki?
- Czy Android App ID w `app.json` jest prawdziwy (nie testowy)?
- Czy iOS App ID jest PRAWDZIWY (v3: iOS live z realnymi reklamami od 1.1.9 — testowy `ca-app-pub-394025...` w prod = bug na OBU platformach, nie oczekiwany stan)?
- **Per-format ad unit IDs**: dla każdego formatu (banner, interstitial, rewarded, app-open) sprawdź czy `__DEV__` branch używa TestIds, prod używa real ID. **TestIds w prod = $0 revenue + AdMob policy violation.**
- Czy reklamy są poprawnie ukryte dla Premium userów? (server-authoritative tier check)
- **Sentry instrumentation per-format** (NOWE): banner / interstitial / rewarded / app-open — każdy MUSI mieć Sentry capture na fail (nie tylko `console.warn`)

### Audyt strategiczny — KIEDY reklamy się pokazują:
Dla każdego miejsca gdzie jest reklama, oceń:
- **Timing:** Czy to naturalny moment przerwy, czy przerywa flow?
- **Frequency:** Jak często user widzi reklamę?
- **Context:** Czy user jest w trybie emocjonalnym (kłótnia) gdy widzi reklamę?

### Compliance:
- Czy jest zgoda na reklamy (ATT na iOS, UMP/Consent Mode na Android)?
- **EU UMP requirement**: od stycznia 2024 Google wymaga UMP SDK dla EEA users. `requestNonPersonalizedAdsOnly: true` NIE zastępuje
- Czy reklamy nie pokazują się dzieciom (COPPA)?

---

## AGENT 3: DESIGN I UI/UX

### Layout i wyświetlanie:
- Sprawdź KAŻDY ekran pod kątem SafeAreaView (czy treść jest obcięta przez notch?)
- Sprawdź KAŻDY ekran pod kątem KeyboardAvoidingView (czy klawiatura zasłania input?)
- Sprawdź czy ScrollView jest wszędzie tam gdzie treść może przekroczyć ekran
- Sprawdź loading / error / empty states dla każdej operacji async

### Visual pattern compliance (NOWE — krytyczne dla nowych screens):
- **Wszystkie nowe screens MUSZĄ używać**: `AuroraBackground` + `GlassCard` (gdzie pasuje) + `GradButton` zamiast raw `TouchableOpacity` z bg color + `useTheme()` zamiast static `colors`
- Flag KAŻDY nowy screen który bypassuje Aurora pattern — wymaga uzasadnienia
- Sprawdź szczególnie: deep-link landing pages (np. `app/reset-password.tsx`, `app/confirm.tsx`) — często pomijane bo "tylko 300ms"

### Dark mode:
- Wyszukaj WSZYSTKIE hardcoded hex kolory (`#[0-9A-Fa-f]{3,6}`) w plikach .tsx
- Sprawdź czy każdy kolor jest zdefiniowany zarówno w light jak i dark wariancie theme
- **Splash screens przed ThemeProvider mount**: muszą używać `useColorScheme` + `lightColors`/`darkColors` raw, nie static `colors`

### Typografia i teksty:
- Czy długie imiona partnerów nie psują layoutu? (sprawdź `numberOfLines` na display_name renders)
- Czy error messages są czytelne i zrozumiałe dla użytkownika?

### Accessibility (NOWE — wzmocnione):
- Wyszukaj wszystkie `TouchableOpacity` i `Pressable` bez `accessibilityLabel`
- **Wszystkie a11y labels MUSZĄ przechodzić przez `t()`** — hardcoded `accessibilityLabel="Email"` to bug (PL screen reader na EN UI mówi "Email", EN na PL mówi "Hasło")
- Sprawdź `accessibilityRole` na icon-only buttons
- Sprawdź touch-target sizes (minimum 44pt)

### Konsystencja:
- Czy spacing jest konsekwentny (czy są "magic numbers" zamiast design tokens)?
- Czy `borderRadius` używa tokens z `lib/theme.ts`?
- Czy ikony są z tej samej rodziny (Ionicons only)?

---

## AGENT 4: INTERNACJONALIZACJA I JĘZYKOZNAWSTWO

### Kompletność tłumaczeń:
- Porównaj WSZYSTKIE klucze w `pl.ts` z `en.ts` — raportuj różnice w obu kierunkach
- Sprawdź czy TypeScript `DeepStringify` wymusza identyczną strukturę
- Wyszukaj WSZYSTKIE polskie słowa hardcoded w plikach .tsx (poza komentarzami) — grep `[ąćęłńóśźż]` w string literals
- Wyszukaj WSZYSTKIE inline `lang === "en" ? ... : ...` ternaries — powinny być przez `t()` (poza locale codes typu `"en-US" / "pl-PL"`)
- Sprawdź `app.json` — czy permission strings są bilingual?

### Jakość PL — konkretny grammar checklist (NOWE):
**KAŻDY nowy klucz PL przeanalizuj pod kątem typowych błędów:**
- **Noun-adjective gender agreement**: `"Mieszane chmury"` (n.) vs `"Mieszanie chmury"` (rzeczownik odsłowny — błąd)
- **Aspekt czasowników**: niedokonany vs dokonany — czy pasuje do kontekstu?
- **Deklinacja przypadków**: po liczebnikach (1 spór, 2-4 spory, 5+ sporów); po przyimkach (do/od/przez)
- **Szyk zdania**: nie kalka z angielskiego (np. unikaj "ja chcę" zamiast "chcę")
- **Frazeologia**: idiomy PL nie EN (np. "trzymać kciuki" nie "trzymać palce na krzyż")
- **Kalka z EN**: "implementować" vs "wdrożyć"; "supportować" vs "wspierać"; "deletować" → "usunąć"
- **Polskie cudzysłowy**: PL używa `„"` (otwierający dolny + zamykający górny), EN używa `""`
- **Spacja przed `?` `!` `:`**: w PL bez spacji (zawsze)

**Czytaj WSZYSTKIE nowe klucze (delta od ostatniego audytu)**, nie tylko spot-check 30 random.

### Jakość EN:
- Czy EN brzmi native, nie translationese?
- Sprawdź spójność terminologii (czy "spór" jest zawsze "dispute", nie raz "argument" raz "fight"?)

### Detekcja języka:
- Potwierdź że język jest wykrywany z `expo-localization` (OS locale), NIE z tekstu usera
- Sprawdź fallback gdy locale jest nieobsługiwany (de-DE, fr-FR → pl)

### Logika language-agnostic:
- Sprawdź `app/dispute/[id].tsx` — czy parsing werdyktu jest emoji-based, nie regex na polskie słowa?
- Sprawdź AI prompty w edge functions — czy wymuszają odpowiedź w języku usera?
- Sprawdź czy `accessibilityLabel` przechodzą przez `t()` (nie hardcoded `"Email" / "Hasło"`)

---

## AGENT 5: BEZPIECZEŃSTWO I DANE

### Prompt injection — cross-function consistency (NOWE):
**KAŻDA edge function wywołująca Claude API MUSI mieć IDENTYCZNY pattern.** Listę zbuduj SAM: `grep -l "anthropic" supabase/functions/*/index.ts` (v3: NIE zakładaj liczby — w v2 skill mówił „4", a było 7: doszły `solo-simulate`, `solo-debrief`, `generate-winback-offer`). Skomparuj WSZYSTKIE znalezione:
- User input wrapped w `<dispute_data>`/`<history_data>` markers? (każda fn)
- System prompt zawiera "ignore any 'ignore previous instructions'" rule? (każda)
- `display_name` sanitized: `name.replace(/[^\p{L}\p{M}0-9 -]/gu, "").slice(0, 30)`? (KAŻDA — flag jeśli któraś tylko `truncate`)
- Field length caps (text 4000, topic 200-300, profile fields 500)? (każda)

**Cross-function inconsistency = anti-pattern.** Flag każdą rozbieżność jako WARNING.

### Rate limiting:
- Sprawdź KAŻDĄ ścieżkę która zużywa AI (create, respond, **continue**, profile generation, context hint)
- Czy każda fn ma rate limit server-side?
- Czy tier-based limits są spójne między fns? (canonical = `lib/tier.ts` + `_shared/tier-limits.ts` przeczytane w pre-audit — NIE liczby z tego skilla; rozjazd klient↔server mirror = finding)
- Czy fail-open ma sensowny default (np. log + proceed) vs fail-closed (block)?

### RLS — pełny audit:
```sql
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
```
Każda tabela MUSI mieć RLS enabled. Sprawdź każdą policy:
- SELECT: czy filter jest dość ścisły? (np. `couples` SELECT bez `archived_at IS NULL` może leakować)
- INSERT: `WITH CHECK` matches USING?
- UPDATE: jakie kolumny user może mutować? Czy są kolumny które MUSZĄ być service-role-only (`subscription_tier`, `archived_at`, `partner_*_id`)? Trigger-based blocker?
- DELETE: kto może usuwać?

### Trigger audit (NOWE):
- Lista wszystkich triggerów: `SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public'`
- Każdy `SECURITY DEFINER` trigger: czy `search_path` jest hardened (`SET search_path = public, pg_temp`)?
- Czy trigger functions referencjonują kolumny które mogą zniknąć (column drop coordination)?

### Sensitive data in logs (NOWE — wzmocnione):
- Grep `console.log` w edge fns dla user text (`text_a`, `text_b`, `topic`, `bio`, `fears`)
- **Grep `debug_logs` insert payloads** — KAŻDY `trace()` call inspect for PII (display names liczą się jako PII pod RODO; lengths OK)
- Sprawdź `Sentry.captureException` `extra` field — czy nie wycieka user content?

### Secrets i klucze:
- Wyszukaj `sk-ant-`, `sk_live_`, `eyJ` w kodzie
- Sprawdź `.gitignore` — czy `.env`, `credentials.json`, `*.keystore`, `google-services.json`, `GoogleService-Info.plist`, `*-service-account.json` są wykluczone?
- Sprawdź EAS secrets — czy wszystkie potrzebne env są w `.github/workflows/*.yml`?

### Auth contract:
- Bare `supabase.functions.invoke()` poza `lib/invoke-edge.ts` — powinno być ZERO
- `verify_jwt: true/false` per fn — udokumentowane w header komentarzu?
- Service-role calls — używają `crypto.timingSafeEqual` lub equivalent constant-time compare?

### Atomowość:
- Czy partner pairing używa atomic operation (RPC lub unique constraint)?
- Czy `Math.random()` jest zastąpiony przez `crypto.getRandomValues()` w sensitive contexts (invite tokens)?

---

## AGENT 6: SUBSKRYPCJE I MONETYZACJA

### Status implementacji:
- Czy `handleSubscribe` robi prawdziwy zakup IAP, czy stub?
- Czy IAP gated przez `EXPO_PUBLIC_IAP_ENABLED` flag?
- Restore purchases (Apple requirement)?

### Logika subskrypcji — server-authoritative (v3: model HYBRYDOWY per-user):
- `SubscriptionContext` czyta `myTier` z `profiles.subscription_*` (gate reklam/solo) + `effectiveTier` z RPC `effective_tier_for_user` = max-of-pair (gate sporów/głębi) — NIE z RC SDK. Kanon: `memory/tech_state.md`.
- Czy policy/trigger blokują client-side mutation `subscription_*` na OBU tabelach (`profiles` I `couples`)? (krytyczne — bez tego user może self-grant Premium)
- RC webhook + sync-subscription: dual-write profil+couple spójny? Payer discriminator (`rc_app_user_id = id`) poprawny (lesson_backfill_payer_discriminator)?
- Server-side limit enforcement w KAŻDEJ AI edge function (nie client-only)?
- Co się dzieje gdy user przekroczy limit? Paywall blur+CTA, nie hard block?

### Bonus analyses (NOWE):
- Czy `bonus_analyses` table + `grant_bonus_analysis` RPC istnieją w migracjach? (audit historyczny: były pre-existing schema drift)
- Czy RPC ma SECURITY DEFINER + auth check (caller is partner_a/b of couple)?
- Daily cap egzekwowany w RPC?

### Free vs Premium — feature gating:
Zweryfikuj listę feature'ów i sprawdź czy każdy jest poprawnie gated server-side:
- Dashboard statystyk → wszyscy
- Profil emocjonalny → wszyscy
- Pełne Gottman/NVC → server zwraca pełną analizę zawsze; tylko UI blur dla free?
- Historia sporów → wszyscy
- Voice recording → Premium (jeśli zaimplementowane)?

---

## AGENT 7: INTEGRACJE I INFRASTRUKTURA

### Supabase:
- Status wszystkich Edge Functions (ACTIVE? wersja?)
- Sprawdź logi edge functions za ostatnie 24h — czy są błędy 5xx?
- Realtime subscription na dispute status działa?
- Migracje aplikowane: porównaj `supabase/migrations/` z migration history table w prod

### Push notifications:
- `EXPO_PUSH_TOKEN` zapisywany przez `register-push-token` edge fn (NIE bezpośrednio w `_layout.tsx` — RLS race)?
- Token format validation `startsWith("ExponentPushToken[")` po obu stronach (klient + serwer)?
- Notification channel dla Androida skonfigurowany?
- Tap routing: cold-start + warm + dispute_id w payload routes do `/dispute/<id>`?

### EAS Build:
- `eas.json` profile development/preview/production poprawne?
- `app.json` ↔ `package.json` version match?
- `versionCode` inkrementowany przed prod build?
- Adaptive icon, notification icon (white silhouette transparent bg)?

### GitHub Actions workflow:
- `.github/workflows/build-android.yml` używa `eas build --local`?
- Decoduje `GOOGLE_SERVICES_JSON_B64` w `eas-build-pre-install`?
- Wszystkie `EXPO_PUBLIC_*` env vars exposed w workflow `env:` block (Sentry DSN, PostHog, RevenueCat)?

### Sentry:
- Inicjalizowany przed renderowaniem apki (`import "../lib/sentry"` przed JSX)?
- ErrorBoundary wysyła do Sentry?
- PII scrubber w `beforeSend` (text_a/b, fears, bio)?

### Dependencies:
- `npm audit` — krytyczne podatności?
- `expo-doctor` — zgłasza problemy?
- Wszystkie paczki kompatybilne z Expo SDK X.Y?

### Publikacja — wymagania sklepów:
**Google Play:**
- `app.json`: tylko potrzebne `android.permissions`?
- Privacy URL w Play Console (manualnie ustawiany)?

**App Store (v3: apka LIVE od 1.1.9):**
- Realny iOS AdMob App ID w binarce (testowy w prod = bug — patrz Agent 2)
- `NSCameraUsageDescription` per-locale?
- Wersja w review / TestFlight vs `app_config.recommended_version_code` iOS — spójne z release-shepherd (nie bumpować przed ruchem Sentry)

---

## AGENT 8: HISTORIA BŁĘDÓW + REPO-WIDE ANTI-PATTERN SWEEP (NOWE)

Przeczytaj WSZYSTKIE `lesson_*.md` w pamięci + `feedback_*.md` + ostatnie podsumowania sesji.

### Verification: czy znane fixy nadal w miejscu?
Dla każdego znanego bugfixa sprawdź:
1. Czy fix jest nadal w kodzie (nie został przypadkowo cofnięty)?
2. Lista konkretnych weryfikacji z lessons (model ID, sanitization, FK cascade, etc.)

### Repo-wide sweep dla każdego anti-patternu (NOWE — krytyczne):

**Dla KAŻDEGO `lesson_*.md`** zrób grep całego repo i wylistuj WSZYSTKIE instancje. Format:

```
Anti-pattern: <nazwa z lesson>
Pre-existing instances (znane historycznie): [file:line, ...]
NEW instances (wprowadzone od ostatniego audytu): [file:line, ...]
Status: ✅ all fixed / 🔴 N new instances / ⚠️ pattern repeated in NEW code
```

**v3 — NIE dubluj CI.** Wzorce gate'owane w `pr-checks.yml` na każdym PR (bare invoke, pinned model snapshots, deprecated FileSystem API, single-curly w translations, bare `subscription_tier` reads, SECURITY DEFINER bez REVOKE w nowych migracjach, sekrety/gitleaks, rozmiar MEMORY.md) sprawdzasz JEDNYM ruchem: `gh run list --workflow "PR Checks" --limit 5` — wszystkie zielone = te klasy czyste; czerwony run = finding. Sweepuj grep'em TYLKO wzorce NIEgate'owane:
- **`if (!user) return;` w onPress handlers** (lesson_dead_buttons_silent_returns) — repo-wide grep
- **`await supabase.from(...).update(...)` / `.insert(...)` BEZ `{ error }` destructure** — repo-wide grep
- **Polish quotes `„"` w TS literals** bez escape (lesson_i18next_interpolation)
- **Push tokens bez `startsWith("ExponentPushToken[")` filter** (lesson_push_token_format)
- **Inline `lang === "en"` ternaries dla UI text** — zostają tylko locale codes
- **Hardcoded `accessibilityLabel="..."` z PL/EN słowami** zamiast `t('a11y.*')`
- **`__DEV__` gates wokół monetyzacji** (lesson_dev_gate_monetization) — powinno być ZERO
- **`canOpenURL` dla custom schemes na Android** bez `<queries>` (lesson_linking_android11)
- **Hardcoded hex `#XXXXXX`** w `app/`/`lib/components/` poza `lib/theme.ts`
- **`track()` przed `router.replace/push` bez `await flushAnalytics()`** (lesson_flush_analytics_before_nav)
- **Nowe lekcje z ostatnich tygodni** — przejrzyj `memory/MEMORY.md` deltę i dodaj sweep dla świeżych patternów, których tu nie ma

### Pattern memo (NOWE):
Po sweep'ie, dla KAŻDEGO patternu który występuje 2+ razy w NEW code, dodaj propozycję:
- Lint rule (eslint custom)
- Helper function (`mustSucceed(...)`)
- TypeScript constraint (utility type)

---

## AGENT 9: SCHEMA DRIFT DETECTOR (NOWY w v2)

**Cross-check live DB vs repo migrations.**

### Krok 1: Inventory live schema (via MCP execute_sql):

```sql
-- Tables
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE'
ORDER BY table_name;

-- RPCs (procedures + functions)
SELECT proname, pronargs FROM pg_proc
WHERE pronamespace = 'public'::regnamespace
ORDER BY proname;

-- Triggers
SELECT trigger_name, event_object_table FROM information_schema.triggers
WHERE trigger_schema='public'
ORDER BY trigger_name;

-- Policies
SELECT tablename, policyname, cmd FROM pg_policies
WHERE schemaname='public'
ORDER BY tablename, policyname;

-- Columns per table (for column drift detection)
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema='public'
ORDER BY table_name, ordinal_position;
```

### Krok 2: Cross-reference z `supabase/migrations/`:
- Read wszystkie pliki `.sql` w `supabase/migrations/` (włącznie z baseline `00000000000000_initial_schema.sql`)
- Wyciągnij definicje tables / RPCs / triggers / policies / columns
- **Compare** z live snapshot:
  - Tables w prod ALE nie w migracjach → schema drift, flag jako ⚠️
  - Tables w migracjach ALE nie w prod → migration not applied, flag
  - Same dla RPCs / triggers / policies / columns
  - Column types mismatch → drift

### Krok 3: Code references vs live schema:
- Grep `supabase.from('X')` w `app/`, `lib/`, `supabase/functions/` — lista tabel używanych przez code
- Grep `.rpc('X')` — lista RPCs używanych przez code
- Każde reference MUSI istnieć w live schema (inaczej code wywoła 404/500)
- Każde reference powinno być też w migracjach (inaczej fresh clone padnie)

### Output:
```
SCHEMA DRIFT REPORT

🔴 In prod but missing from migrations:
- Table: bonus_analyses
- RPC: grant_bonus_analysis(uuid)
- Trigger: ...

🔴 In migrations but missing from prod (migration not applied):
- ...

⚠️ Column type / nullability mismatch:
- couples.subscription_tier: prod = text, migration = varchar

✅ In sync: N tables, N RPCs, N triggers, N policies
```

---

## AGENT 10: LIFECYCLE MATRIX / RODO PER-EVENT (NOWY w v2)

**Sprawdź cleanup contracts per-lifecycle-event, nie tylko delete-account.**

### Events do audytu:

Per event wypełnij macierz:

| Event | Tables modified | Data deleted | Data preserved | Cross-partner PII access AFTER | Notifications |
|---|---|---|---|---|---|
| signup | profiles, couples? | - | - | - | - |
| email_confirm | auth.users | - | - | - | - |
| couple_create | couples, profiles | - | - | - | - |
| pair_invite_create | pair_invites | - | - | - | - |
| pair_invite_redeem | pair_invites, couples, profiles | - | - | - | - |
| dispute_create | disputes | - | - | - | push to partner |
| dispute_respond | disputes | - | - | - | push to creator |
| dispute_reveal | disputes | - | - | - | - |
| dispute_analyze | disputes, debug_logs | - | - | - | push to both |
| **pair_unpair (consensual)** | couples (archive), profiles, **emotional_profiles?**, push_tokens? | ? | ? | **CHECK: czy ex-partner czyta drugiego emotional_profile?** | push to survivor |
| **partner_deleted** (one-sided) | couples (archive), auth.users | cascade chain | survivor's data | survivor sees archived couple | push to survivor |
| **account_delete** (full RODO) | wszystkie tabele | wszystko user-owned | nic | nic | push to partner |

### Per cell sprawdź:

**Tables modified:**
- Lista tabel zmodyfikowanych przez edge fn lub trigger
- Cross-check z code (read edge fn source)

**Data deleted:**
- Co jest fizycznie usunięte
- ON DELETE CASCADE chain (wymaga schema reading)

**Data preserved:**
- Co zostaje (intentionally lub niezauważone)
- Czy preserved data zawiera PII drugiej osoby?

**Cross-partner PII access AFTER event** (KRYTYCZNE):
- Po evencie, czy któraś strona ma dostęp do PII drugiej której NIE powinna?
- Sprawdź RLS policies dla każdej tabeli z PII (`profiles`, `emotional_profiles`, `disputes` text_a/b, `bonus_analyses` granted_to)
- 90-day archive window — czy enforced server-side (RLS), czy tylko client-side (UI hides)?

**Notifications:**
- Czy survivor / pozostała strona dostaje push?
- Czy notification ujawnia coś co nie powinno (np. "Anna usunęła konto" = ujawnia że Anna była w tej parze)?

### Output:
```
LIFECYCLE MATRIX REPORT

🔴 RODO leaks (PII persists where it shouldn't):
- pair_unpair: emotional_profiles NOT deleted; ex-partner reads other's fears indefinitely

🟡 Soft cleanup gaps (90-day cutoff client-only):
- archived couples: 90-day grace enforced w `useArchivedCouple` hook only; SQL ma no cutoff

✅ Clean: account_delete cascades correctly; ...
```

---

## AGENT 11: ANALYTICS & OBSERVABILITY (NOWY w v3)

**Warstwa telemetrii dryfuje niezależnie od kodu — audytuj kontrakt end-to-end.**

### Rejestr eventów vs rzeczywistość:
- Źródło prawdy: `EntityEventProps` w `lib/analytics.ts` (typed registry, PR #290). Wylistuj wszystkie eventy.
- Cross-check z live definicjami PostHog (MCP `read-data-schema kind:events`): eventy w registry bez definicji → sprawdź ile było OKAZJI (query DB), zanim nazwiesz to luką (lesson_automation_prompt_names_drift — n≈1 to pustynia danych, nie bug).
- Eventy w PostHog, których nie ma w registry → legacy/dryf nazw, flaguj.
- Każdy entity-scoped event ma `entity_id` (lesson_event_entity_id_property)?

### Konsumenci nazw eventów (dryf wielopunktowy):
- Prompt routine `kmr-daily-digest` (memory/reference_routines.md) — czy pyta o istniejące nazwy?
- GA4: custom dimensions zarejestrowane w Admin (lesson_ga4_custom_dimension_registration)? `fbLog*` mirror events na wszystkich ścieżkach (lesson_lifecycle_event_on_all_paths)?
- Dashboardy/insighty PostHog odwołujące się do martwych eventów.

### Observability:
- Sentry `beforeSend` scrubber pokrywa NOWE pola PII (text_a/b, fears, bio + pola z nowych feature'ów: solo transcript?)
- `debug_logs` trace() w nowych fns — PII-free?
- Firebase consent mirror lazy-init (lesson_firebase_consent_mirror_race) nadal w miejscu?

### Output:
```
ANALYTICS CONTRACT REPORT
🔴 Registry↔PostHog↔digest rozjazdy: [...]
🟡 Eventy bez okazji do ingestu (expected, monitor): [...]
✅ In sync: N eventów / scrubbery / dimensions
```

---

## WERYFIKACJA FINDINGÓW (v3 — OBOWIĄZKOWA przed raportem)

Po zebraniu raportów 11 agentów, ZANIM napiszesz raport zbiorczy:
1. **Każdy BLOCKER i WARNING potwierdź zewnętrznie**: przeczytaj wskazany file:line własnym Read/Grep (nie ufaj raportowi subagenta — lesson_subagent_output_verification). Niepotwierdzony → wyrzuć lub obniż do INFO z adnotacją „(niepotwierdzone)".
2. **Cross-check z decisions ledger**: finding pokrywający się ze świadomą decyzją → przenieś do sekcji „Świadome stany (ledger)" — NIE do blokerów. Przykłady klas: email confirm OFF, brak definicji eventu przy zerowym ruchu, zawieszone kampanie.
3. **Dedup między agentami**: to samo znalezisko z 2+ agentów = jeden wpis (z listą agentów, którzy je widzieli — to sygnał wagi, nie mnożnik liczby).

## FORMAT RAPORTU ZBIORCZEGO

Po zebraniu wyników wszystkich 11 agentów i przejściu WERYFIKACJI FINDINGÓW, dostarcz raport w tym formacie:

```
═══════════════════════════════════════════════
PEŁNY AUDYT — Kto Ma Rację?
Data: [data] · Wersja: [X.Y.Z]
═══════════════════════════════════════════════

🔴 BLOKERY (nie publikuj bez naprawy)
[lista z plikiem:linią i szacowanym nakładem pracy]
**Per blocker oznacz**: pre-existing | introduced-by-Faza-N

🟡 OSTRZEŻENIA (napraw przed closed testing)
[lista z plikiem:linią]

🟢 INFO (popraw kiedy będzie okazja)
[lista]

✅ CO DZIAŁA DOBRZE
[lista potwierdzonych mechanik]

📊 STATYSTYKI AUDYTU
- TypeScript errors: X
- Translation key parity: X = X (PL ↔ EN)
- Hardcoded PL/EN strings in app/.tsx: X
- Inline lang === "en" ternaries (excl. locale codes): X
- Screens without SafeAreaView: X
- Buttons without accessibilityLabel: X
- Console.log of user text in edge fns: X
- AI edge fns without rate limit: X
- Tables without RLS: X
- Schema drift items: X
- Bare supabase.functions.invoke() outside invoke-edge.ts: X
- Pinned Claude snapshots: X
- Silent .from().update() without { error }: X

🔁 FIX-INDUCED REGRESSIONS (NOWA SEKCJA)
Z poprzednich faz fix, które wprowadzone bugi:
- B2 (Faza 1): invokeEdge response shape change broke dispute UI handler
- W16 (Faza 1): reset-password.tsx skipped Aurora pattern
- ...

🔁 ANTI-PATTERN REPO-WIDE SWEEP (NOWA SEKCJA)
Per known lesson_*.md anti-pattern:
- silent_returns: 5 instances [list], 0 new since last audit
- bare_supabase_invoke: 0 instances ✅
- ...

🔁 CROSS-CUTTING CONSISTENCY (NOWA SEKCJA)
- AI edge fns sanitization: 3/4 use canonical pattern, 1 (generate-profile) only truncates
- Error response shapes: limit_exceeded vs analysis_failed have different shapes
- New screens visual pattern: 4/5 use Aurora; reset-password.tsx bypasses
- ...

🔁 SCHEMA DRIFT (NOWA SEKCJA)
- ...

🔁 LIFECYCLE MATRIX (NOWA SEKCJA)
- ...

📋 PLAN NAPRAWY
Faza 1 (przed publikacją): [lista z czasem]
Faza 2 (przed closed testing): [lista z czasem]
Faza 3 (post-launch): [lista z czasem]

🧠 ŚWIADOME STANY (decisions ledger — NIE blokery)
[findingi przeklasyfikowane przez ledger, ze źródłem decyzji]

SZACOWANY CZAS NAPRAWY BLOKERÓW: X godzin
WERDYKT: PRODUCTION HEALTHY / WYMAGA NAPRAWY (X blokerów)
```

### Wynik audytu → mózg (v3)

Po dostarczeniu raportu dopisz skrót do vaulta `D:\SecondBrain\projekty\kmr-audyty.md` (utwórz przy pierwszym audycie: frontmatter `typ: notatka, tagi: [kmr, audyt], powstalo, zrodlo: sesja-code` + `Gałąź: [[kto-ma-racje]]`). Wpis per audyt: data · werdykt · liczby (blokery/warningi/info) · top-3 findingi · link do pełnego raportu w repo. Mózg widzi TREND audytów, a poniedziałkowa meta-nauka ma z czego korzystać.

---

## INSTRUKCJE DLA CLAUDE CODE

### Przed dispatch agentów:
1. Read CLAUDE.md, ostatnie commits w git log, wszystkie `lesson_*.md` w pamięci
2. Sprawdź version w `package.json` + `app.json` (flag mismatch)
3. Sprawdź czy są pending PRs / niedeployowane fns

### W trakcie:
1. Nie skracaj raportu — każde znalezisko z numerem linii i plikiem
2. Nie zakładaj że coś działa — sprawdź kod
3. Jeśli nie możesz sprawdzić czegoś (np. runtime behavior) — zaznacz "WYMAGA MANUALNEGO TESTU"
4. Priorytetyzuj bezpieczeństwo i dane użytkowników nad estetyką
5. Porównaj z historią — czy naprawione bugi nie wróciły?
6. **Distinguish pre-existing vs introduced-by-FazaN** — pomocne dla retrospekcji

### Subagent self-verification standards (NOWE — wymagaj w prompcie):
Każdy subagent prompt MUSI zawierać sekcję:

```
Verification checklist (MUST report in summary):
1. Paste exact `npx tsc --noEmit` output
2. Grep for all callers of changed APIs (paste file:line list)
3. For new code paths: simulate happy path mentally + walk through each step
4. For new screens: verify follows Aurora pattern (AuroraBackground/GlassCard/GradButton)
5. For changed contracts: list every consumer + verify they handle new shape
6. For DB changes: verify trigger/policy implications across other tables
7. Anti-pattern sweep: if fixing instance of known anti-pattern, grep entire codebase, fix ALL
```

### Po raporcie:
- Zapytaj: "Chcesz żebym naprawił Fazę 1 teraz?"
- Po fix-phase: 24h cooldown + targeted re-audit na CHANGED code paths
- Nie ufaj subagent self-report; verify externally
- **Po każdej fazie merge'd → invoke `lessons-update` skill** żeby wyciągnąć anti-patterns / fix-induced regressions / surprises i zapisać do `memory/` jako lessons. To zwiększa baseline dla kolejnych sesji (auto-load via SessionStart hook).

### Cadence rule (do MEMORY.md):
- Po każdym fix-phase: focused re-audit zmienionych ścieżek
- Po każdym subagent run: grep dla nowych anti-patternów które subagent mógł wprowadzić
- Visual consistency check (Aurora) na nowych screens
- Contract change → grep callerów

---

## CHANGELOG SKILLA

**v3 (2026-07-04)** — po analizie krytycznej skilla (sesja 2026-07-04; root cause = klasa lesson_automation_prompt_names_drift):
- **Decisions ledger z mózgu**: pre-audit czyta `memory/project_*.md` + huby vaulta (kto-ma-racje/kmr-growth/google-ads/ASA) + najnowszy digest; ledger wstrzykiwany każdemu agentowi; nowa sekcja raportu „Świadome stany"
- **Derive, don't hardcode**: usunięte zgniłe stałe (capy „7/wk,50/mo,100/mo" → lib/tier.ts; „4 fns AI" → grep, było 7; couples.subscription_tier → hybryda per-user; „iOS testowy AdMob ID oczekiwany" → iOS live, odwrócona logika)
- **Weryfikacja findingów** przed raportem: external confirm każdego BLOCKER/WARNING + cross z ledgerem + dedup
- **Agent 11: Analytics & observability** (registry↔PostHog↔digest↔GA4 + scrubbery)
- **Agent 8 odchudzony**: nie dubluje wzorców gate'owanych w CI pr-checks.yml (weryfikuje tylko zieloność runów)
- **Agent 1**: ścieżki solo/Trening, social login, win-back/referral
- **Tryb delta** (opcjonalny) + werdykt „PRODUCTION HEALTHY" zamiast „GOTOWY DO PUBLIKACJI" + skrót audytu do vaulta (`kmr-audyty.md`)

**v2 (2026-05-01)** — po retrospektywie pełnego cyklu audyt + 5 fix-phases:
- Dodany Agent 9: Schema drift detector (cross-reference live DB vs migrations)
- Dodany Agent 10: Lifecycle matrix / RODO per-event audit
- Wzmocniony Agent 5: cross-function consistency check, debug_logs PII audit
- Wzmocniony Agent 8: repo-wide anti-pattern sweep (nie tylko targeted check), pattern memo
- Wzmocniony Agent 1: state machine completeness, routing destination mutability, silent return repo sweep
- Wzmocniony Agent 4: konkretny PL grammar checklist, czytanie WSZYSTKICH nowych kluczy
- Wzmocniony Agent 3: visual pattern compliance (Aurora) dla nowych screens, splash-before-ThemeProvider
- Nowe sekcje raportu: Fix-induced regressions, Anti-pattern repo-wide sweep, Cross-cutting consistency, Schema drift, Lifecycle matrix
- Subagent verification standards (paste tsc output, grep callers, simulate path)
- Distinguish pre-existing vs introduced-by-FazaN
- Cadence rule (24h re-audit po fix-phase)
