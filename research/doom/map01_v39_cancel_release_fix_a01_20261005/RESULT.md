# Result

Disposition: **PASS_CANDIDATE_MECHANICS**. The candidate emits per-key release measurement for confirmed owner cleanup, joins it to the original actuation ID and program/step context, and drains owner records on every execute exit. Cancellation still performs ordered owner-state reconciliation; query failures propagate while recorded measurements are preserved. Already-recorded expiry cleanup is forwarded without requiring a cancellation event.

The current scoped suites pass 11 focused candidate tests (including owner-side aggregate-query fault injection), 3 current-main ExecutorV12 composition tests, including both aggregate-query fault cases, 10 InputOwner compatibility tests, and 2 existing v39 bridge tests on bundled CPython 3.12.14. The source-locked auditor validates all 26 receipts, including retained RED/GREEN outputs for both aggregate-query faults. The exact-current-main replay is retained in `current-main-post-r135-replay-a07.log`.

The current-main ExecutorV12 expiry-to-terminal composition passed on `bfd182727aebd9636c6a84fb437848c1dfe66be8`; the standalone run log is `executor-v12-expiry-suite.log`.

This remains fake-display evidence. It does not characterize cleanup still pending after execute exits, live X11/application behavior, independently useful feedback, bounded recovery efficacy, gameplay, safety, latency, or a live allocation. It is not an integrated runtime PASS.

The owner persists the per-key release rows before its aggregate pointer/keymap queries. If either query raises, the confirmed per-key receipt remains drainable, the partial owner-release row remains `verified=false` without sampled `keys_down`, and the original query exception still propagates.

Through ExecutorV12 expiry, both aggregate-query fault regressions retain one contextual confirmed-up receipt and a verified-empty terminal barrier; see the A07 RED/GREEN output in the package.

The A08 lifecycle regressions now pass on top of the current PR's pointer-query, keymap-query, and ExecutorV12 composition coverage: 12 focused tests, an optimized 12-test repeat, 3 ExecutorV12 compositions, 10 owner compatibility tests, and 2 existing bridge tests. The source lock remains pinned to `bfd182727aebd9636c6a84fb437848c1dfe66be8`. Results remain local fake-display mechanics only.


A fake-display focus-invalidation schedule also confirms the terminal barrier drains the independently recorded `focus_changed` release after the execute-exit drain, before the needs-decision terminal. The prior bridge yields zero such receipts; the candidate emits one confirmed contextual up and verifies empty state. Verification now covers 13 candidate tests, 13 optimized, 3 ExecutorV12, 10 owner compatibility, 2 bridge, 29 primary receipts, and 95 manifest entries.


## A10 — current-head owner-ledger retirement

The exact PR #7805 head `61502e45d40b67b6d588b4e8357e42fde05a9dbe` reproduced the #7823 finding: after a confirmed F8 up followed by aggregate keymap failure, the partial release receipt was preserved but a later `b` request under the same lease was still injected. With the owner-ledger patch rebased, the confirmed edge retires the internal held entry, aggregate failure faults and clears the active lease, and the later request is rejected before injection.

The bundled CPython 3.12.14 suites pass 14 focused tests, 14 optimized-mode focused tests, 3 ExecutorV12 compositions, 10 owner compatibility tests, and 2 bridge tests. The current-main source audit and package checksum verification are recorded separately. This remains fake-display candidate evidence only.

During independent PR review, a clean-checkout audit defect was found: the committed tree lacked the RED/GREEN A10 logs required by `audit.py`. Those outputs are now retained and reproduced with the exact pinned baseline source and candidate source on Windows CPython 3.11.9. Baseline RED confirms the second DOWN was admitted; candidate GREEN rejects it. The original CPython 3.12.14 suite evidence is unchanged.