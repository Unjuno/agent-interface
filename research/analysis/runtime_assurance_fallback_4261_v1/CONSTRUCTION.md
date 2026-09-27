# Construction history

- construction-01 executed the initial eight-scenario development table. Candidate/raw audit passed, but the sixth corruption control (`remove_row`) caused an auditor KeyError instead of returning a typed integrity failure. This is a construction harness failure; no formal identity existed.
- Repair changed only auditor missing-row handling so malformed evidence returns HOLD_OR_FAIL. Scientific plant/controller/monitor/fallback rules were unchanged.
- construction-02 re-executed the same development table: candidate audit PASS; corruption controls 6/6 reject; unit tests 3/3 pass. This entire development table is excluded from formal.
- Because construction-02 exercised all development schedules, the formal denominator is a prospectively frozen, previously unexecuted held-out grid: x0={2,3,4} × drift onset={0,2} × duration={2,5}, two late-result controls, one nominal control, and one fallback-unavailable YIELD control. The mechanism, safety bound, monitor margin, fallback, progress definition and decision rule are unchanged. No formal held-out row has been executed before freeze.
