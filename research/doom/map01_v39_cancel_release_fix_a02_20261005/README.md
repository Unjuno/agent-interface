# V39 release-evidence durability A02

This additive fake-display candidate covers two observed loss boundaries in the PR #7805 cancellation-receipt path. The original A01 package and PR are unchanged.

The owner now persists per-key measurements in an `owner_release` record even when the later aggregate neutral-state query raises. In that case it records `verified=false`, `verification_status=UNAVAILABLE`, and unknown aggregate key/button state; it re-raises the query error. The bridge still publishes the independently confirmed per-key up row. It does not claim overall neutral state from that row.

The bridge also drains owner records after the executor's final `release_all()` barrier. The executor test uses current `ExecutorV3`, a fake display, the candidate InputOwner, and a test backend barrier that synchronously calls `owner.release`, matching the existing owner-release contract. It checks that the confirmed up is emitted before the expired terminal and that the fake display and bridge ledger are empty.

## H/T/D/C/U

**H — owner query failure.** If the aggregate `query_keymap()` fails after the owner sampled a successful per-key release, the per-key row must remain observable while aggregate neutrality remains unverified.

**T.** The fake display injects failure at query 5, after F8 admission and the release pre/post samples. Compare the unmodified A01 InputOwner source with the A02 source using the same focused test. The candidate/compatibility/bridge suites then exercise the A02 copy.

**D.** PASS requires one `CONFIRMED_PHYSICAL_UP` row for F8, a durable owner record with `verified=false`, `verification_status=UNAVAILABLE`, null aggregate state, an empty bridge-held set for the confirmed F8 up, and an empty fake physical set. The aggregate exception must still propagate.

**C.** A deterministic fault-injected fake display is not a failed real X server. The failure occurs in global reconciliation after per-key up evidence has been sampled.

**U.** No real X11, physical OS input, application consumption, GUI/game effect, live allocation, safety, latency, or task benefit was tested.

**H — final executor barrier.** An owner release completed by ExecutorV3's synchronous final release barrier must still be published when it occurs after `Backend.execute()` has already drained its records.

**T.** Against the same fake display and owner candidate, force one admitted F8 hold, expire ExecutorV3, then have its test backend's final barrier call the real candidate `owner.release`. Run once against A01 bridge v2 and once against the A02 bridge.

**D.** PASS requires the pre-fix bridge to emit zero release rows and retain F8 despite a verified owner release; the A02 bridge must emit one contextual confirmed-up row before the single expired terminal and leave both ledgers empty.

**C.** This is ExecutorV3 control flow with a test backend around the current InputOwner candidate. It is not the full V39 session/backend stack and makes no claim about a pending cleanup that has no final owner barrier.

**U.** Fake-display software composition only; no live X11 or Issue #59 threat-control outcome.

## Reproduce

From repository root, use CPython 3.11+:

```powershell
python research/doom/map01_v39_cancel_release_fix_a02_20261005/run_expiry_red.py
python -m unittest research.doom.map01_v39_cancel_release_fix_a02_20261005.test_cancel_release.CancellationReceiptTests.test_executor_expiry_terminal_contains_one_verified_cleanup_receipt -v
python research/doom/map01_v39_cancel_release_fix_a02_20261005/run_candidate_suite.py
python research/doom/map01_v39_cancel_release_fix_a02_20261005/run_owner_compat_suite.py
python -m unittest discover -s research/doom/map01_v39_perkey_bridge_a01 -p 'test_*.py' -v
python research/doom/map01_v39_cancel_release_fix_a02_20261005/audit.py
```

The retained successful runs were performed on Windows 11 Home, CPython 3.11.9. WSLc was not invoked because the WSL-backed service had unknown active ownership; the available C: space was under 700 MB. These local checks are not container-equivalent. All test doubles use fake display objects and import stubs.

`candidate-suite-attempt01-harness-miswire.*`, `expiry-attempt02-harness-miswire.*`, `expiry-attempt01-harness-miswire.*`, and `expiry-diagnostic.*` preserve verification setup variants that selected the wrong bridge/source path or modeled the final barrier as a state-only query. Their outcomes are excluded from the A02 PASS; `TDD_RED_RECEIPT.md` records how each was classified. No A01 source or evidence was edited.
