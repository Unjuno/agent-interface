# A13 STOP — candidate ran before freeze

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309)
- Allocation: `5309-PRECAPTURE-CONTROL-A13-20261007`
- Disposition: `STOP_PREFREEZE_CANDIDATE_EXECUTED`; no scientific verdict.
- Formal-stage counts: candidate 1 (host, before freeze), environment 0, auditor 0.

The candidate invocation preceded any source/input/gate checksum freeze and cannot count as a valid formal run. It was not repeated. The retained candidate-choice JSON, command details, limitations, planned H/T/D/C/U, separate container runtime smoke, and exact SHA-256 values are in [PRE_FREEZE_STOP.md](PRE_FREEZE_STOP.md). This STOP preserves the failed procedure; it is not evidence for or against the hypothesis.
