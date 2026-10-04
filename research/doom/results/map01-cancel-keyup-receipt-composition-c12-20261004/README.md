# C12 — cancellation cause and per-key release receipt composition

## H / T / D / C / U

**H.** The two open #59 paths can coexist at the owner boundary: retain PR #7441's explicit owner-thread key-up receipt, and when cancellation arrives during owner release I/O, preserve PR #7440's final cancellation-cause recheck.

**T.** Pin current main and both PR heads. Derive a test-only owner source from PR #7441's exact `input_owner_v12.py`, inserting PR #7440's three-line post-`query_keymap()` cancellation recheck before the owner-release receipt is recorded. Run an added same-owner key-up/cancel-during-sync integration case, the PR #7441 backend provenance tests, and the two-key batch positive/negative controls. Run the retained executor-cancel publication regression in its own process because its fake Xlib modules are process-global test fixtures.

**D.** PASS only if six composition tests and one separately isolated publication control pass; the explicit up has exactly one identity-bound XTest/XSync receipt; cancellation injected during release sync yields a verified empty `owner_release(reason=cancelled)` and the lease records that cause; and the retained batch controls preserve step provenance while rejecting missing or duplicate history.

**C.** The new integration case instantiates the candidate owner and transition wrapper with a fake Xlib display, then injects cancellation during the release synchronization call. The executor terminal-order case uses the PR #7440 test's controlled queue and fake backend. The typed release-batch tests use their existing synthetic owner fixtures.

**U.** This is host-side software construction with synthetic Xlib/backend state. It does not test a live X server, physical key-up, application/game feedback, useful recovery, performance, or MAP01. It is not a resolution of the three add/add file conflicts between the PR heads: the combined owner is an additive local derivation only, and no production file or PR head was changed.

## Result

`PASS_COMPOSITION_SCOPED`: six composition tests and a separate one-test publication control pass. The same owner instance records the explicit key-up receipt and, when cancellation is injected during a later release `sync()`, records a verified empty cancellation release. The lease's first interruption cause is `cancelled`. The backend's existing synthetic positive and negative batch controls also pass. An initial combined-process run is retained as `raw/initial-combined-suite-*`; its publication-control test failed while looking for `input_released`. The frozen runner now runs that control in a separate process, where it passes.

Source closure, test command, raw output and both per-process exit receipts are retained here. Line-ending-normalized `input_owner_v12.py` snapshots from PR #7440 and PR #7441 are included under `FROZEN/`; their source commits, original Git blob IDs, and archived-file SHA-256 values are recorded in `FREEZE.json` and `SOURCE_PINS.json`. The audit verifies that the candidate owner is exactly the frozen PR #7441 owner with only the documented three-line cancellation recheck added, and that PR #7440's frozen source contains that recheck. The exact refs are current main `75c6d18888da68033ef4b07cffefb3622568ed19`, PR #7440 `99b7d130742b4e884709a862bc074d15e6b42ac9`, and PR #7441 `a5fec2be836afd21134db31d2dbf8be651e52c68`.

No live allocation, model, game, X server, physical input, scorer, container or GPU was used. Issue #59's per-key live measurements, independently useful feedback, matched recovery and real-time threat-control gates remain open.

## Reproduction

From this directory:

```powershell
python -B run_c12.py
python -B audit_c12.py
python -B -m unittest test_audit_c12.py
```

The unit tests exercise the audit only; they do not rerun the composition experiment or contact a live X server.
