# Issue #2858 Chromium navigation-readiness Rung0 — frozen plan

## Scope
Fresh mechanism-screen under #2858. This is not a rerun of #2416 and cannot close #2858: it replaces the historical six-task HTTP fixture with Chromium-internal pages and has no held-out second desktop surface. It isolates whether the two 100 ms pauses around omnibox text are discriminating under fresh versus sequential navigation and idle versus same-CPU contention.

## H
Within at least one fixed {FRESH|SEQUENTIAL}×{IDLE|CONTENDED} stratum, NO_EXTRA_WAIT will fail both fresh measurements while FIXED_100MS succeeds both. REOBSERVE_ACTIVE is a non-sleep comparator that performs current active-window round trips after Ctrl+L and after text but does not inspect omnibox text.

## T
3 policies ×2 loads ×2 phases ×2 repetitions =24 fresh private Xvfb/Openbox/Chromium sessions, one scored navigation per session. FRESH measures about:blank→chrome://settings/. SEQUENTIAL first establishes chrome://settings/ using a common FIXED_100MS setup route, then scores chrome://settings/→chrome://downloads/. IDLE has no extra load. CONTENDED runs one busy loop pinned to the same logical CPU inherited by Xvfb/Openbox/Chromium. Each scored navigation uses focus-preserving Ctrl+L, URL text, Enter; timeout 3 s; no replay. Independent readiness evidence is DevTools page URL plus current Chromium active-window identity. Setup failures are integrity failures; scored timeouts/crashes are scientific outcomes.

## D
Integrity:24 complete measurement receipts, common sequential setup ready, exact policy/load/phase identities, typed scored failures, monotonic order for ready outcomes, owned process receipts. `PASS_FIXED_WAIT_DISCRIMINATES_SCOPED` only if at least one stratum has NO_EXTRA_WAIT ready=0/2 and FIXED_100MS ready=2/2. Otherwise complete evidence => `HOLD_WAIT_BENEFIT_NOT_ESTABLISHED`. Regardless of PASS/HOLD, full #2858 remains open because historical fixture/root cause and held-out transfer are not tested.

## C
Chromium internal pages and DevTools scoring are not the historical fixture. XTEST event ordering may make fixed waits unnecessary; sequential internal pages may have their own lifecycle. CPU contention is synthetic and host frequency/load are uncontrolled. REOBSERVE_ACTIVE adds X round trips and only checks window identity, not omnibox readiness.

## U
Historical run-1 cause, exact six-task page readiness, focus/window replacement, second application, natural failure rate, model/task/tokens, cross-platform behavior remain unknown.

## Variables / units
No inferential formula is used. `t` timestamps are monotonic nanoseconds (ns); reported duration is milliseconds (ms = ns/1e6). Counts are dimensionless integers. Policy/load/phase are categorical. Timing is diagnostic; no calibrated measurement uncertainty or SLO is claimed.
