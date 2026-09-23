# Condition-based staggered sub-agent starts

Issue: #3158

## H/T/D/C/U

- H: typed release conditions can delay consequential starts without unnecessarily serializing independent low-risk work.
- T: fixed-seed Docker experiment comparing IMMEDIATE, FIXED_STAGGER, CONDITION_STAGGER, and SERIAL_CRITICAL over independent, resource-conflict, stale, predecessor-failure, duplicate, cancellation, and deadline scenarios; recompute every row with an independent auditor.
- D: image agent-interface-2994:20260920, digest sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c, network none, seed 3158, model/network calls 0.
- C: PASS_STAGGERED_SUBAGENT_ORCHESTRATION_SCOPED. CONDITION_STAGGER started only independent low-risk work and denied all six unsafe conditions. IMMEDIATE and FIXED_STAGGER exposed unsafe starts; SERIAL_CRITICAL was safe but serialized the independent control. Policy-filtered independent audit matched the retained rows.
- U: deterministic orchestration simulation scope only; no claim about actual model sub-agents, GUI actions, general scheduling, or production latency. The first run had an auditor policy-filter bug and is not used as the formal result; the correction is described by provenance in the runner history.

The result distinguishes typed release conditions from elapsed-time delay.
