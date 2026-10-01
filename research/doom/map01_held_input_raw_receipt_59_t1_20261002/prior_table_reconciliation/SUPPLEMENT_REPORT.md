# Prior-table reconciliation result

Disposition: **`PASS_PRIOR_TABLE_RECONCILED`**, limited to cross-document consistency.

The one formal comparator invocation matched all **38/38** completed decision rows (v38 11/11, v39 27/27) after rounding candidate row measurements to exactly the prior table's displayed 0.001 ms. All **18/18** exact aggregate fields matched within the frozen 1e-9 ms tolerance; derived overshoot fractions matched; and the v39 interrupted receipt matched identity, requested duration, keys, acknowledgment and verified-empty timestamps, and the 212.579736 ms interval. The interruption remains excluded from completed-hold totals. No errors were reported.

This supplement used the already-retained #6198 candidate JSON and the exact SHA/blob-pinned #6175 `AUDITED_INTERVALS.json`. Candidate invocations: 0. Original auditor invocations: 0. Supplemental comparator invocations: 1. Retries: 0. The seven synthetic comparator tests passed before the formal invocation. The input identities, invocation count, full checks and output digest are recorded in `RECONCILIATION_FREEZE.json`, `RECONCILIATION.json`, and `SUPPLEMENT_RUN.json`.

## Scope and limitations

The prior #6175 table identifies itself as a **posthoc machine-readable transcription** of the prior report, not the original candidate JSON. Therefore this pass shows that the retained #6198 outputs agree with that published transcription under its display-rounding and aggregate-tolerance rules; it does not independently validate the transcription against missing original #6175 receipts, nor does it repair those missing receipts. No candidate or original auditor rerun was performed.

This does not establish physical keymap occupancy, exact ordinary key-up time, task-useful feedback, a causal v38/v39 comparison, live safety, game success, latency benefit, or product benefit. Docker Desktop was not used: its service was stopped and the engine unavailable; the read-only comparator has no container-dependent semantics and no shared allocation was altered.
