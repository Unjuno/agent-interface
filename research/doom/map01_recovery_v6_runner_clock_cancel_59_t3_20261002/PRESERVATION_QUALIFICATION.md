# Historical T3 STOP preservation qualification (2026-10-02)

The original freeze-order protocol STOP and all eight published files remain unchanged. This is retained invalid-run evidence, not a promotable research pass.

The standalone construction arm summary has start/end timestamps `109395097120000` / `109395175834000`, while the summary embedded in construction_result.json has `109441503508900` / `109441564975100`. Their common execution provenance is unestablished. Both are preserved; the discrepancy alone does not establish a specific invocation count.

The initial construction failure is narrative-only in REPORT.md; no corresponding stderr/traceback receipt or independent auditor result is among the eight original files. Candidate/retry counts are recorded harness declarations rather than an independent invocation ledger.

The clock-return marker is sampled before the separate timestamp returned to the runner and is not identical to planner_window.end_ns. A's reported 0.111 ms delay refers to marker-to-backend cancellation observation, not marker-to-cancel-request time.

No source, raw output, gate or historical disposition was repaired or regraded. No candidate, auditor, tests or live work was rerun or authorized by this preservation merge.
