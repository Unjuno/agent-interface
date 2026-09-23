# Safe probe identification successor (#1978)

Decision: PASS_SAFE_PROBE_IDENTIFICATION_SCOPED

H/T/D:
- Full 3-state x 2-action deterministic table universe: 729 automata.
- All 256 passive coverage masks.
- Candidate class counts and post-probe partitions computed exactly.
- Exhaustive information-gain choice; with independent transition cells all admissible unknown pairs tie, so deterministic first-unknown tie-break is used.
- Selected probe is always within the declared safe set.
- No-probe/empty-safe cases preserve UNKNOWN; safe-set exclusion rejected 228 candidate states.
- Deliberate digest corruption detected.
- formal=1, audit=1, reruns=0, tuning=0.

C/U:
This is a finite passive automaton fixture. It does not establish safety of probes in real applications, hidden-state handling, nondeterminism, reachability, model quality, GUI correctness, latency, token cost, or production transfer. Probe safety is an explicit declared input, not discovered. Stop after this one-shot formal/audit.

Additive path only: research/analysis/safe_probe_identification_successor_1716_v1/**
