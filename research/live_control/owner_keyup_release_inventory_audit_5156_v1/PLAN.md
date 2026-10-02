# Allocation 06 — expected release-inventory completeness (synthetic construction)

## H / T / D / C / U

**H.** An audit that is supplied an independently frozen admission/release inventory can reject an empty owner trace, omitted release brackets, a missing admission or terminal, and identity/timestamp corruption while preserving the exact pinned InputOwner v10/v11 key request and XSync sequence. The current Allocation-03 raw auditor's per-row validity checks do not establish completeness.

**T.** Freeze current main and exact PR #5298 v11 owner, v10 control, v3 caller wrapper, and Allocation-03 tests/auditor. Run the pinned fake-Xlib owner test suite and one ordered synthetic session with three accepted key-downs, one explicit up, a two-key aggregate cleanup, and three verified-empty owner terminals. Compare baseline and candidate auditors on pristine and deletion controls; independently audit the resulting raw trace in a separate process. No retry.

**D.** `PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION_SYNTHETIC_ONLY` requires: pinned owner suite 14/14; v10/v11 request sequence, XSync count and final fake key state match; candidate accepts pristine trace; candidate rejects empty/all-bracket omission/one-bracket deletion/missing-admission/missing-terminal/keycode/timestamp mutations; baseline false-accepts the omitted-bracket controls; separate raw-only audit returns errors=[]. Anything else is FAIL or STOP as appropriate.

**C.** CPython host execution with deterministic fake Xlib and stub exception classes only. No Docker/OrbStack, real X server, GUI, physical input, game, model, GPU or network. The shared container allocation remains unassigned in #5085; this source-only gate does not claim that allocation.

**U.** The fixture is synthetic. Owner v11 has no stable per-actuation identifier; repeated identical key/intent events remain correlated by expected order/count rather than a runtime actuation ID. This does not establish physical held-input occupancy, live release completeness, MAP01 behavior, useful feedback, recovery cover or human-tempo benefit. A formal X11 run still requires a fresh exact-main freeze and a named shared-resource lease.
