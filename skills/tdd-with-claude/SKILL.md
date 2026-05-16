---
name: tdd-with-claude
description: Use when implementing any new feature, bug fix, or refactoring where tests should drive design. Enforces explicit red-green-refactor prompting because Claude defaults to implementation-first. Includes anti-patterns, RN/Supabase-specific patterns, real-world example sessions from kto-ma-racje, integration with TodoWrite, Plan Mode, hooks, and sub-agents.
---

# TDD with Claude Code

> **Confidence**: Tier 1 — Based on official Anthropic best practices, community validation, and ~30 production bugs in kto-ma-racje that TDD would have caught (or honestly wouldn't have — see "When TDD won't catch it").

Test-Driven Development with Claude requires explicit prompting. Claude naturally writes implementation first, then tests. TDD requires the inverse.

---

## Table of Contents

1. [TL;DR](#tldr)
2. [The Problem](#the-problem)
3. [Setup](#setup)
4. [Mobile RN / Expo-specific TDD](#mobile-rn--expo-specific-tdd)
5. [The Red-Green-Refactor Cycle](#the-red-green-refactor-cycle)
6. [Integration with Claude Code Features](#integration-with-claude-code-features)
7. [Anti-Patterns](#anti-patterns)
8. [When TDD won't catch it (and what to do instead)](#when-tdd-wont-catch-it-and-what-to-do-instead)
9. [Advanced Patterns](#advanced-patterns)
10. [Real kto-ma-racje example sessions](#real-kto-ma-racje-example-sessions)
11. [See Also](#see-also)

---

## TL;DR

```
Red → Green → Refactor

But you MUST prompt Claude explicitly:
"Write a FAILING test for [feature]. Do NOT write implementation yet."
```

For React Native + Supabase apps specifically:
- Test the **rendered state user actually sees**, not just function return values.
- Cover the full state machine: `loading → success → error → empty → racy`.
- Mock native modules (push, IAP, deep links) early — they're the most expensive to debug in production.

---

## The Problem

Without explicit instruction, Claude will:
1. Write implementation code
2. Then write tests that pass against that implementation

This defeats TDD's purpose: tests should drive design, not validate existing code.

A deeper issue specific to React Native: many bugs are **state-not-thrown** — UI is stuck on a spinner or shows "Nieznany" but no error fires. `tsc --noEmit` passes, Sentry is clean, manual inspection of the function says "looks fine." Only TDD against rendered output catches these.

---

## Setup

### CLAUDE.md Configuration

Add to your project's CLAUDE.md:

```markdown
## Testing Conventions

### TDD Workflow
- Always write failing tests BEFORE implementation
- Use AAA pattern: Arrange-Act-Assert
- One assertion per test when possible
- Test names describe behavior: "should_return_empty_when_no_items"

### Test-First Rules
- When I ask for a feature, write tests first
- Tests should FAIL initially (no implementation exists)
- Only after tests are written, implement minimal code to pass

### React Native screen TDD
- Cover the full state matrix per screen: loading, success, error, empty
- Test the rendered output (React Native Testing Library), not just function returns
- Mock native modules (expo-notifications, react-native-purchases, expo-linking) in setup
- For useEffect side effects: write a "still pending after N ticks" failing test
```

### Hook for Auto-Run Tests (Optional)

Create `.claude/hooks/test-on-save.sh`:

```bash
#!/bin/bash
# Auto-run tests when test files change
if [[ "$1" == *test* ]] || [[ "$1" == *spec* ]]; then
  npm test --watchAll=false 2>&1 | head -20
fi
```

---

## Mobile RN / Expo-specific TDD

Most TDD literature targets pure functions. Mobile apps live and die by **stateful UI + async side effects + native modules** — and that's where most of our production bugs land. Below: patterns that earn their keep.

### Pattern 1: Test the rendered state, not the return value

A function can return the right shape and the UI can still be broken. Test what the user sees.

```ts
// ❌ Weak — tests internal shape, misses state-not-thrown bugs
test("fetchProfile returns boolean", async () => {
  expect(await fetchProfile("uuid")).toBe(true);
});

// ✅ Strong — tests what user sees
test("ProfileScreen renders display_name after fetch resolves", async () => {
  render(<AuthProvider><ProfileScreen /></AuthProvider>);
  await waitFor(() =>
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument()
  );
  expect(screen.getByText("Mirek")).toBeInTheDocument();
});

// ✅ Even stronger — explicit anti-deadlock
test("ProfileScreen does NOT stay on spinner forever", async () => {
  render(<AuthProvider><ProfileScreen /></AuthProvider>);
  // If side effect deadlocks (effect guard always falsy on first render),
  // this assertion fails because loading text never disappears.
  await waitFor(
    () => expect(screen.queryByText("Loading...")).not.toBeInTheDocument(),
    { timeout: 3000 }
  );
});
```

The "does NOT stay on spinner" pattern would have caught the **pair-show spinner deadlock** that shipped in PR #159 (initial state `creating=true` made `!creating` guard always false → side effect never ran → infinite spinner). Reference: `memory/lesson_useeffect_guard_shared_with_ui_state.md`.

### Pattern 2: Cover the full state matrix per screen

Every async screen has at least 4 states. Most bugs hide in 2 of them.

| State | What user sees | Common bugs |
|---|---|---|
| Loading | Spinner | Deadlock (effect never fires), no timeout, infinite |
| Success | Real data | Stale data, partial render, profile=null with session present |
| Error | Friendly message + retry | Silent return, white screen, dead button |
| Empty | "No items yet" CTA | Confused with loading, missing copy |
| Racy | First-paint-after-resume | Stale closure, double-fire, lost event |

Write one failing test per state **before** implementation. The empty + racy columns are where production bugs hide.

### Pattern 3: useEffect side-effect testing

`useEffect` with guards is the single highest-density bug source in our codebase. Three failure modes:

1. **Effect never fires** — guard always falsy on first render (initial state shared with UI flag)
2. **Effect fires twice** — React StrictMode double-mount, or unstable dependency
3. **Effect captures stale closure** — async function inside useEffect captures `state` at mount time, not at re-render

For each, write a failing test that asserts side-effect ran exactly once and rendered output changed:

```ts
test("createInvite fires exactly once on mount when no seed params", async () => {
  const spy = jest.spyOn(api, "pairCreateInvite");
  render(<PairShowScreen />);
  await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
  // If guard is broken (shared state), this fails with 0 calls.
  // If StrictMode double-fire breaks idempotency, fails with 2.
});
```

### Pattern 4: Mock native modules early, not after they break in production

`expo-notifications`, `react-native-purchases`, `expo-linking` — every native module silently returns useless values in Jest unless mocked. Write the mock as part of the failing test, not as a fix after Sentry pings you.

```ts
// __mocks__/expo-notifications.ts
export const getPermissionsAsync = jest.fn().mockResolvedValue({ status: "granted" });
export const requestPermissionsAsync = jest.fn().mockResolvedValue({ status: "granted" });
export const getExpoPushTokenAsync = jest.fn().mockResolvedValue({
  data: "ExponentPushToken[mock-token-123]",
});
```

Then test the denial path explicitly:

```ts
test("registerForPush silently skips when permission denied", async () => {
  (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValueOnce({
    status: "denied",
  });
  const result = await registerForPushNotifications("user-uuid");
  expect(result).toBeNull();
  expect(saveToken).not.toHaveBeenCalled();
});
```

That denial test would have caught the [`KTO-MA-RACJE-J/-3` push-permission-info captureMessage anti-pattern](memory/lesson_useeffect_guard_shared_with_ui_state.md) earlier — the test would either need to assert "no Sentry issue created" (catching the noise) or "breadcrumb fires" (catching the cleanup direction).

### Pattern 5: Realtime / race-condition tests

Supabase Realtime + concurrent triggers ≠ deterministic. Use fake timers + manually-fired events.

```ts
test("dispute self-heal does NOT fire twice when both partners trigger", async () => {
  jest.useFakeTimers();
  const triggerSpy = jest.spyOn(api, "selfHealDispute");

  // Both partners trigger 5ms apart (typical Realtime fanout)
  const [p1, p2] = [partnerAClient(), partnerBClient()];
  p1.emit("status_change", { ... });
  jest.advanceTimersByTime(5);
  p2.emit("status_change", { ... });

  await flushPromises();
  expect(triggerSpy).toHaveBeenCalledTimes(1);
  // If atomic-UPDATE-WHERE-RETURNING is broken, fails with 2.
});
```

This pattern would have caught the [Realtime double-trigger bug](memory/lesson_realtime_race_concurrent_triggers.md) before the 2x Anthropic spend.

---

## The Red-Green-Refactor Cycle

### Phase 1: Red (Write Failing Test)

**Prompt**:
```
Write a failing test for [feature description].
Do NOT write the implementation yet.
The test should fail because the function/method doesn't exist.
```

**Example**:
```
Write a failing test for a function that calculates the total price
of items in a cart, applying a 10% discount if total exceeds $100.
Do NOT implement the function yet.
```

**Expected Claude behavior**:
- Creates test file with test cases
- Tests reference function that doesn't exist
- Running tests would fail with "function not defined" or similar

**Verification**:
```bash
npm test  # Should fail with "calculateCartTotal is not defined"
```

### Phase 2: Green (Minimal Implementation)

**Prompt**:
```
Now implement the minimum code to make these tests pass.
Only write enough code to pass the current tests, nothing more.
```

**Expected Claude behavior**:
- Creates implementation file
- Writes minimal code to satisfy tests
- Avoids over-engineering

**Verification**:
```bash
npm test  # Should pass
```

### Phase 3: Refactor (Clean Up)

**Prompt**:
```
Refactor the implementation to improve code quality.
Tests must stay green after refactoring.
Focus on: [readability / performance / removing duplication]
```

**Expected Claude behavior**:
- Improves code without changing behavior
- Runs tests to verify they still pass
- Documents any significant changes

---

## Integration with Claude Code Features

### With TodoWrite

Track TDD phases in your task list:

```
User: "Implement user authentication with TDD"

Claude creates todos:
- [ ] RED: Write failing tests for login
- [ ] GREEN: Implement login to pass tests
- [ ] REFACTOR: Clean up login implementation
- [ ] RED: Write failing tests for logout
- [ ] GREEN: Implement logout
- [ ] REFACTOR: Clean up
```

### With Plan Mode

Use planning for test strategy:

```
[Press Shift+Tab to enter Plan Mode]

I need to implement a shopping cart with TDD.
Plan the test cases before we start writing any code.
```

Claude will explore codebase in read-only mode, then propose test plan before any implementation.

### With Hooks

Auto-run tests after edits using a PostToolUse hook:

```json
// In .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "npm test --watchAll=false 2>&1 | head -20"
      }
    ]
  }
}
```

### With Sub-Agents

Delegate test writing to scope-focused agent:

```
Use the test-writer agent to create comprehensive tests for
the UserService class, covering all edge cases.
Then I'll implement to pass those tests.
```

### With pre-deploy-audit skill

The kto-ma-racje pre-deploy-audit skill (13 checks) is the **last gate** before deploy. TDD is the **first gate** — tests written before implementation. They compose:

- TDD catches design-level bugs early (wrong shape, missing state)
- pre-deploy-audit catches integration-level bugs late (RLS leaks, secrets, hardcoded strings)

If TDD passes but pre-deploy-audit fails, you skipped integration testing. If TDD test was never written, pre-deploy-audit becomes the only safety net — and several of our production bugs slipped past it because they were state-not-thrown.

### With session-summary skill

End-of-session, `session-summary` writes the day's lessons to `memory/`. Any lesson that includes "TDD would have caught this" should trigger an update to this skill's [Anti-Patterns](#anti-patterns) and [Real example sessions](#real-kto-ma-racje-example-sessions) sections — living document, not static.

---

## Anti-Patterns

### What NOT to do

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| "Write tests for this feature" | Claude implements first | "Write FAILING tests that don't exist yet" |
| "Add tests and implementation" | Loses test-first benefit | Separate into two prompts |
| "Make sure tests pass" | Encourages implementation-first | "Write tests, then implement minimally" |
| Skipping refactor phase | Accumulates technical debt | Always refactor after green |
| Multiple features at once | Loses focus | One feature per TDD cycle |
| **Shared state for UI flag + effect guard** | First-render deadlock, side effect never fires | Separate `loading` (UI) and `hasStarted` (effect) states |
| **Testing function return only** | Misses state-not-thrown bugs (profile=null with session) | Test rendered output via React Native Testing Library |
| **Implicit native module behavior** | Real iOS prompt diverges from Jest default | Mock `expo-notifications` / `react-native-purchases` in `__mocks__/` |

### Common Mistakes

**Mistake**: Asking Claude to "test" existing code.
```
# Wrong
"Write tests for the existing calculateTotal function"

# Right
"Write tests for calculateTotal behavior, assuming function doesn't exist.
Then we'll verify the existing implementation passes."
```

**Mistake**: Combining red and green phases.
```
# Wrong
"Implement calculateTotal with tests"

# Right
"Write failing tests for calculateTotal. Stop there."
[After tests written]
"Now implement to pass those tests."
```

**Mistake**: Sharing initial state between UI flag and effect guard.
```ts
// ❌ Wrong — !creating is FALSE on first render → effect never fires
const [creating, setCreating] = useState(!hasSeed);
useEffect(() => {
  if (!hasSeed && !creating) doWork();
}, []);

// ✅ Right — guard on "have we produced result?", not on UI flag
const [result, setResult] = useState(null);
const [loading, setLoading] = useState(false);
useEffect(() => {
  if (!hasSeed && !result) {
    setLoading(true);
    doWork().then(setResult).finally(() => setLoading(false));
  }
}, []);
```

This anti-pattern shipped in PR #159 (pair-show.tsx) and lived <2 hours in production before user feedback caught it. A 5-line React Native Testing Library test would have caught it pre-merge. See `memory/lesson_useeffect_guard_shared_with_ui_state.md`.

**Mistake**: Trusting subagent self-report.
```
# Wrong
"Subagent says: TS clean + tests pass + verified"
[Merge without re-verification]

# Right
"Run the actual commands yourself and paste output."
```

State-not-thrown bugs slip past subagent verification. See `memory/lesson_audit_self_report_distrust.md`.

---

## When TDD won't catch it (and what to do instead)

TDD is powerful but not omnipotent. Honest list of bug classes where it didn't help us:

### 1. iOS-only navigation behavior

PR #131: root `<Slot />` in expo-router → iOS back gesture dead, router.back no-op. Android masked it via system back button. **Tests passed on jest-expo runner because RN testing doesn't distinguish iOS from Android navigator behavior.** Only first TestFlight build revealed it.

**Mitigation**: For nav/router changes, add manual smoke test "back per platform" to pre-release smoke checklist. Don't rely on TDD alone for native gesture behavior.

### 2. JWT race conditions with Supabase

Tests run with a stable JWT in memory. Production has a 1-hour TTL access token + lazy refresh, OS-killed processes, AsyncStorage cold reads. **No reasonable test setup replicates this fully** — you'd need to model Supabase JS internals.

**Mitigation**: Defense-in-depth — 10s `Promise.race` timeout in fetchProfile, retry-once on RLS 401, AppState listener that force-refreshes on background → foreground after >5min. See `memory/lesson_auth_bootstrap_signin_race.md`, `lesson_supabase_onauth_event_filter.md`.

### 3. OS process killing after long background

Android low-memory killer / iOS background timeout (30+ min) kills the RN process. Cold remount races silent token refresh. **Tests don't model process death.**

**Mitigation**: Production-only bug. Mitigated by AppState listener + bootstrap timeout/retry (PR #155). Discovery: USER FEEDBACK > automation.

### 4. Cron / cache TTL bugs

Realtime channel suspension during IAP dialog, 30-day tier_override TTL, cache invalidation. **Test setups use fake timers but real bug is wall-clock-dependent.**

**Mitigation**: TDD for the resolution logic (does max(self, partner) work correctly?), manual smoke for the wall-clock paths.

### 5. Third-party SDK initialization races

RevenueCat offerings empty on first launch, Firebase Analytics not yet ready, AdMob consent prompt timing. **Mocking these adequately is more work than the code being tested.**

**Mitigation**: Integration test with real SDK in a TestFlight/internal-track build. Don't aim for unit-test coverage here.

### What to write instead when TDD can't help

- **Production smoke test checklist** — pre-release manual test of 6-8 critical flows on a real device
- **Sentry breadcrumbs** — `addBreadcrumb` (not `captureMessage` — breadcrumbs don't create issues) along auth flow so when production fails you have the timeline
- **PostHog routine** — daily check of activation funnel, drop-off rates, signal/noise in errors
- **debug_logs table** — server-side trace pattern for edge functions (per `memory/lesson_debug_logs_pattern.md`)

---

## Advanced Patterns

### Property-Based Testing

```
Write property-based tests for the sort function.
Properties to test:
- Output length equals input length
- All input elements exist in output
- Output is ordered
Use fast-check or similar library.
```

Property-based testing for our domain — `getEffectiveTier(self, partner)`:

```
Properties to test for getEffectiveTier:
- Idempotent: getEffectiveTier(getEffectiveTier(x, y), x) === getEffectiveTier(x, y)
- Commutative: getEffectiveTier(a, b) === getEffectiveTier(b, a)
- Monotonic: getEffectiveTier(free, pro) === pro
- Override never demotes: getEffectiveTier(pro + override basic) === pro
```

These are exactly the invariants that `lib/tier.ts` claims in comments but never proves under fast-check.

### Mutation Testing

```
After tests pass, run mutation testing to find weak spots.
Identify tests that don't catch mutations.
```

> **Going further**: JiTTesting applies mutation testing automatically at PR time — LLM-generated, ephemeral, zero maintenance. Meta deployed this at scale with 4x regression catch improvement over traditional tests. See [Just-in-Time Catching Test Generation at Meta](https://arxiv.org/abs/2601.22832).

### TDD with Legacy Code

```
I need to refactor legacyFunction.
First, write characterization tests that capture current behavior.
Then we'll refactor with confidence.
```

For the **subscription per-user refactor** planned in `memory/project_subscription_per_user_refactor_planned.md`, this is the right pattern:

1. Write characterization tests for current per-couple behavior (analyze-dispute tier resolution, RC webhook target, paywall gate)
2. Verify they pass against current implementation
3. Refactor schema (per-user) — tests fail
4. Implement per-user resolution — tests pass with new semantics

The characterization-first approach is the safest way to refactor revenue-path code.

### State machine TDD for screens

Every async RN screen has a state machine. Test it explicitly:

```ts
describe("PairShowScreen state machine", () => {
  test("loading → success", async () => { /* mount + waitFor data */ });
  test("loading → error → retry → success", async () => { /* mock fail then succeed */ });
  test("expired → regenerate in-place → fresh code", async () => { /* timer + tap */ });
  test("rejected by partner → fresh code without screen transition", async () => { /* realtime + assert */ });
});
```

This is the test plan that PR #159 didn't have. PR #160 fixed the spinner deadlock but the matrix is still untested — write it before refactor B touches subscription logic.

---

## Real kto-ma-racje example sessions

Three concrete bugs from our codebase that TDD would have caught at zero cost. Use these as templates.

### Example 1: pair-show spinner deadlock (PR #159 → #160)

**Bug**: Initial state `creating: true` shared with effect guard `!creating` → effect never fires → infinite spinner.

**TDD that would have caught it**:

```ts
// Red — write this BEFORE implementing pair-show.tsx
test("PairShowScreen shows QR within reasonable time when no seed params", async () => {
  jest.spyOn(api, "pairCreateInvite").mockResolvedValueOnce({
    data: { invite_id: "x", code: "ABC123", token: "tok", expires_at: "..." },
    error: null,
  });
  render(<PairShowScreen />);
  // Initially: spinner OK
  expect(screen.getByTestId("spinner")).toBeInTheDocument();
  // After API resolves: QR present, spinner gone
  await waitFor(() => expect(screen.getByTestId("qr-code")).toBeInTheDocument());
  expect(screen.queryByTestId("spinner")).not.toBeInTheDocument();
});
```

The `waitFor` would timeout if the side effect never fired (the actual bug). 5 lines of test, <2 hours of production downtime avoided.

### Example 2: IAP void for single users (PR #144 + #158)

**Bug**: Single user (no `couple_id`) buys IAP. Google charges, RC webhook fires, schema target is `UPDATE couples WHERE partner_X_id = $userId` → 0 rows → silent no-op. `SubscriptionContext` early-returns `tier="free"`. User loses money "into the void."

**TDD that would have caught it**:

```ts
// Red — characterization test for SubscriptionContext
test("user without couple_id never sees premium tier even after purchase", async () => {
  const profile = { id: "u1", couple_id: null, display_name: "Solo" };
  render(
    <AuthProvider value={{ profile }}>
      <SubscriptionProvider>
        <TierDisplay />
      </SubscriptionProvider>
    </AuthProvider>
  );
  expect(screen.getByText("free")).toBeInTheDocument();

  // Simulate post-purchase refetch:
  await act(() => triggerWebhook({ user_id: "u1", tier: "pro" }));

  // ASSERTION: this test is the requirement spec.
  // Either it should pass (user stays free → reveals architectural gap)
  // Or fail (user becomes pro → forces per-user schema)
  // Writing it BEFORE implementation surfaces the design question.
  expect(screen.getByText("free")).toBeInTheDocument();
});
```

The test forces the question "what should happen here?" before code is written. Answer drives the subscription-per-user refactor decision.

### Example 3: Auth profile fetch race (PR #116)

**Bug**: useEffect fire-and-forget `fetchProfile` + manual `INSERT` colliding with `on_auth_user_created` trigger → profile=null silently, only force-quit fixes it.

**TDD that would have caught it**:

```ts
test("fetchProfile populates state even when trigger creates row in parallel", async () => {
  // Simulate trigger row already existing when client INSERTs
  mockSupabase.from("profiles").select.mockResolvedValueOnce({ data: null, error: null });
  mockSupabase.from("profiles").insert.mockResolvedValueOnce({
    error: { code: "23505", message: "duplicate key" },
  });
  mockSupabase.from("profiles").select.mockResolvedValueOnce({
    data: { id: "u1", display_name: "Trigger Created", invite_code: "ABC" },
    error: null,
  });

  render(<AuthProvider><ProfileScreen /></AuthProvider>);
  await waitFor(() => expect(screen.getByText("Trigger Created")).toBeInTheDocument());
  expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
});
```

Tests the recovery path (UPSERT + re-fetch). The test would fail with the original `INSERT.single()` → `null + error` → `setProfile(null)` cement, forcing the upsert+rehydrate pattern shipped in PR #116.

---

## Example Session (Generic)

### User Request
```
Implement a URL shortener service with TDD.
```

### Phase 1: Red
```
Let's use TDD. First, write failing tests for:
1. Shortening a URL returns a short code
2. Retrieving a short code returns original URL
3. Invalid URLs are rejected
4. Expired links return error

Do NOT implement anything yet.
```

### Phase 2: Green
```
Tests are written and failing. Now implement the minimum
code to make them pass. Use an in-memory store for now.
```

### Phase 3: Refactor
```
Tests pass. Now refactor:
- Extract URL validation to separate function
- Add proper error types
- Improve variable names

Run tests after each change to ensure they stay green.
```

---

## See Also

### Same plugin (kto-ma-racje-toolkit)
- [pre-deploy-audit](../pre-deploy-audit/SKILL.md) — 13-step gate before merge / build
- [full-audit](../full-audit/SKILL.md) — Multi-agent comprehensive audit
- [lessons-update](../lessons-update/SKILL.md) — After each fix-phase, ask whether a lesson should land in `memory/`
- [agent-teams-quick-start](../agent-teams-quick-start/SKILL.md) — Multi-perspective review for high-stakes changes
- [search-tools-mastery](../search-tools-mastery/SKILL.md) — rg vs semantic vs AST — pick the right tool
- [subagent-driven-development](../subagent-driven-development/SKILL.md) — Plan-then-dispatch with two-stage review

### Project skills (versioned in repo)
- `.claude/skills/session-start/SKILL.md` — Beginning of session, gather state
- `.claude/skills/session-summary/SKILL.md` — End of session, write lessons + commit
- `.claude/skills/new-app-architecture/SKILL.md` — Foundations for new mobile projects
- `.claude/skills/supabase-edge-function/SKILL.md` — Boilerplate + patterns

### Repo lessons most relevant to TDD
- `memory/lesson_useeffect_guard_shared_with_ui_state.md` — Spinner deadlock anti-pattern (PR #159→#160)
- `memory/lesson_auth_profile_fetch_race.md` — useEffect fire-and-forget + INSERT race (PR #116)
- `memory/lesson_supabase_onauth_event_filter.md` — TOKEN_REFRESHED filter (PR #135)
- `memory/lesson_audit_self_report_distrust.md` — "TS clean + verified" ≠ "działa"
- `memory/lesson_dead_buttons_silent_returns.md` — `if (!user) return` without Alert
- `memory/lesson_realtime_race_concurrent_triggers.md` — Double-fire from Realtime fanout
- `memory/lesson_anti_pattern_repo_sweep.md` — Found one instance? Grep the whole repo.

### External
- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [JiTTesting at Meta (arxiv)](https://arxiv.org/abs/2601.22832) — LLM-generated mutation testing at PR time
- [Superpowers plugin](https://github.com/obra/superpowers) — Stricter TDD enforcement: code written before failing test gets deleted
