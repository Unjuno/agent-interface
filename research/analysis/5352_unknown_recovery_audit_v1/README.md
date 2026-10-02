# Issue #5352 — exhaustive literal-policy construction audit

Status: formal-03 completed with `STOP_AUDIT_SEMANTIC_MISMATCH`; see [RESULT.md](RESULT.md) and [attempt history](ATTEMPT_HISTORY.md). This does not replace any prior #5352 result.

## Question and literal policy

The retained #5352 plan specifies a hysteresis band (enter at risk `>= 0.70`, exit at risk `<= 0.30`) and treats stale evidence as an immediate escalation that clears hysteresis state. The separate recovery-gain Issue comments mention a `peak_error <= E` envelope and a predictive admission gate, but the actual T6/T7 source and exact gate pseudocode are absent from current main and Issue comments. To avoid inventing those semantics, this audit examines only the earlier explicit literal contract from #5352 T0: numeric confidence/risk levels `{0.64, 0.65, 0.66, 0.69, 0.70, 0.71}`, stale, critical; enter at `.70`, exit at `.65`; stale maps to UNKNOWN; CRITICAL bypasses the band and yields ESCALATED. UNKNOWN has no valid-row rebootstrap rule in the retained description.

## H/T/D/C/U

- **H:** The retained written no-rebootstrap interpretation and simulator transition priority may disagree after UNKNOWN; formal-03 tests this ambiguity.
- **T:** Exhaustively enumerate every sequence of lengths 1 through 6 over the fixed 8-symbol alphabet (`8 + 8^2 + ... + 8^6 = 299,592` traces). For each trace, inspect the first numeric valid observation after each stale symbol. Report traces with stale-then-valid, first-valid outcomes, all later valid rows still UNKNOWN, all critical events and same-row escalations, and canonical counterexamples.
- **D:** Both processes traversed `299,592` traces, but candidate and auditor disagree on state semantics/counters after UNKNOWN. The disposition is STOP, not PASS. See [RESULT.md](RESULT.md).
- **C:** Identical deterministic finite trace set but competing post-UNKNOWN interpretations. Candidate and auditor use separate transition implementations and do not import from each other. This is an exhaustive symbolic count, not a probability estimate.
- **U:** No task truth, calibrated confidence, mode-switch utility, planner latency/cost, bounded recovery-time criterion, or runtime persistence is measured. Results apply only to this one literal state machine. It cannot reproduce or substantiate T7's safety-envelope result because T7's predictive gate semantics/source are unavailable.

## Execution protocol

1. `FREEZE-03.json` records candidate/auditor/Dockerfile/README SHA-256 before formal enumeration.
2. The pinned Python image was built and run with network disabled, read-only root, dropped capabilities, no-new-privileges, PID/memory/CPU limits.
3. Candidate and independent auditor each ran as a separate container invocation.
4. The semantic mismatch is retained as STOP. No source was edited or rerun after that formal allocation.
