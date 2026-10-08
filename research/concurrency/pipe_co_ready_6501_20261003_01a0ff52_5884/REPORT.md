# Native co-ready pipe A01 first result (#6501)

METHOD_PASS_SCOPED / H_PASS_CO_READY_SCOPED. Retain the existing explicit control-priority policy for this decision contract; reject the first-ready simplification. Runtime/portable adoption remains HOLD. No new mechanism is needed.

| Policy | Both-ready decisions | Cancellation-first violations | Data-only / control-only / empty |
|---|---:|---:|---|
| first returned ready entry |4|2 (C001/C006)|2/2 correct each|
| existing control priority |4|0|2/2 correct each|

Observed native ready order matched byte write order in all eight authored co-ready rows, regardless of the two registration orders. This is an observation of this deck, not an OS guarantee. In C001/C006 D was primary work although C was already returned ready; remaining C was drained later only as cleanup. With control priority, C was primary and unread D was separately drained only after the primary checkpoint. Cleanup is not relabelled successful work.

All twenty conditions were retained, including four empty polls. Each row closed and checked its selector plus four owned pipe FDs, with no row-local descriptor reuse. No producer replay, new comparison or success-selected exclusion.

## Provenance and first receipts

- Source freeze commit `7e757470d8ac95faf7a9282fafd05d7b1d03a961`; SHA256 `fae98f3c393456563fe0e118809a279f5d23dfe68ce56816864b232aa5363c40`. Local Git source commit and public prospective freeze5965582128 precede execution.
- Producer: 2026-10-03T04:36:56.654401+00:00 to 2026-10-03T04:36:56.699212+00:00, exit0. Primary raw-only auditor: 2026-10-03T04:36:56.699846+00:00 to 2026-10-03T04:36:56.748676+00:00, exit0. Counts1/1, retries0. Exact commands/cwd/receipts retained in run-01/attempt.json.
- Raw: 81594 bytes, SHA256 `88f79f5c5e3eaec5420c16e3019c20b0f656b06e1cb080c4a1cc133fe4029578`. Explicit stdlib reducer imports no producer or repository runtime; reconstructs prewritten readiness, FD/byte bindings, selected/read/drain order and every close check using a separate truth table.
- Eight predeclared copied controls rejected: boolean_fd, boolean_count, primary_wrong_byte, hidden_control_ready, missing_row, cleanup_relabelled_primary, poll_before_write, unclosed_fd. Original raw before/after SHA remains exact. These are retained-data audits; separate from the primary auditor and not new OS trials.
- Selected runtime: Python3.12.13, macOS27.0.1 arm64, build26A434, KqueueSelector. Frozen selected executable/selectors.py/select-extension pins, no whole kernel/transitive closure claim. One serial stdlib process per producer/auditor. Observed launcher-child peak RSS 20692992 bytes covers Git identity reads and producer/auditor children collectively, not an isolated producer peak.
- Preflight load snapshot [2.623046875, 3.0791015625, 2.96435546875]; later load/clock sync uncertainty unmeasured. UTC/monotonic stamps establish recorded ordering only; no performance estimator or latency gain. Native OS required for the question; no container/daemon was started.

## Qualifications

Finite policy enumeration already proves control-first for a returned ready list. This actual OS residual only demonstrates why first native entry was insufficient in the measured co-ready cells; it is not general singleflight adoption, arbitrary blocking-I/O preemption, a guarantee about cancellation arriving after select, concurrent correctness, process/thread join, portable backend/real workload/GUI/application effect/physical release/model/token savings/authority evidence. Trusted producer instrumentation and standard libraries remain assumptions; nonauthor review is pending.

Construction only: an initial patch-edit exact-line diagnostic and a nonexistent peer source-path read were preserved and repaired before freeze; no source comparison ran during them. AST/preflight and finite enumeration are distinct from the formal allocation. All originally frozen sources/inputs remain byte-exact after raw and copied controls.

Only this inert additive research package is proposed; scripts have .py.txt suffix, no workflow/runtime/import/test-discovery/shared index change. Current-main composition, actual GitHub requirements, prospective two-of-three nonauthor content consensus and an expected-old forward application remain separate. Common deadline unknown/unextended.

Local project checks: public navigation26 documents/1639 links PASS; committed --git-tree workspace inventory PASS. First guessed --strict flag returnedusage/exit2 before checking; exact implemented flag corrected without comparison replay. Initial and corrected receipts/logs retained in local-checks/. No broad runtime suite is needed for inert text/evidence-only additions.
