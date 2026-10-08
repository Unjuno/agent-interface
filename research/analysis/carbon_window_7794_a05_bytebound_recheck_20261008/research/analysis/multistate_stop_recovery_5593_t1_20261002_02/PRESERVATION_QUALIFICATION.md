# Historical multistate-record preservation qualification

This note accompanies PR #6194 at original head `a61a34d17863666a21e3d21a3f5a47059d02a036`. The 24 original T0/T1 package files, sources, fixtures, outputs, manifests and dispositions remain unchanged.

## Receipt-format limits

Both RUN.json candidate.stdout fields use flat key/value summaries, whereas the retained candidate.py sources print JSON. Those fields must not be cited as byte-for-byte console transcripts. The retained RUN commands contain placeholder mount paths. T0's stderr field preserves an exception excerpt, not a full traceback. Execution counts, exit codes and container conditions remain historical recorded assertions; this static preservation review does not independently re-establish the original execution environment.

## Distinct outcomes remain distinct

T0 remains `METHOD_FAIL_AUDIT`: its omitted-episode corruption control trusted the shortened input's denominator, and no audit-result artifact was produced. The [owner failure receipt](https://github.com/Unjuno/agent-interface/issues/5593#issuecomment-5938134553) remains controlling. The [pre-execution auditor amendment](https://github.com/Unjuno/agent-interface/issues/5593#issuecomment-5938108435) explains the initial versus retained auditor hash; no new rewrite is made here.

T1 separately records `PASS_METHOD_MULTISTATE_ROSTER_SCOPED` for a six-ID frozen roster and authored finite-state bookkeeping. Its success does not repair T0 or establish empirical recovery, censoring assumptions, causal benefit, runtime reliability or product safety. The [empirical cohort HOLD](https://github.com/Unjuno/agent-interface/issues/5593#issuecomment-5915621966) remains unresolved; the [T1 owner scope](https://github.com/Unjuno/agent-interface/issues/5593#issuecomment-5938329266) remains unchanged.

No candidate, auditor, construction test, container, hash recomputation or scientific experiment was executed for this preservation review. Index reconciliation retains all current-main entries and adds the two result/failure directories once.
