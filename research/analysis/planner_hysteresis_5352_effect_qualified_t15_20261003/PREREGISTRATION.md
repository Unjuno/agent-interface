# #5352 effect-qualified hysteresis discriminator (T15 method fixture)

Status: preparation/construction only. Candidate and auditor code exist; only zero-seed construction tests have run. No formal candidate, independent audit invocation, or container invocation is claimed.

## H/T/D/C/U

- **H:** On a deliberately finite discriminator fixture, fixed hysteresis can diverge from the raw mode schedule without changing a declared safe terminal effect and can reduce mode-boundary cost; a different divergence can violate a required mode or an intermediate-prefix safety predicate. This is a method-level falsifiable claim, not evidence about real workload prevalence or task benefit.
- **T:** Compare raw threshold, fixed hysteresis (enter risk index >=3, exit <=1), and two-observation minimum dwell on five frozen traces in the T0 symbol alphabet. An independent effect oracle classifies: B1, allowed mode divergence with identical completed effect; H1, required local continuation violated; P1, forbidden escalation on an intermediate prefix despite matching terminal mode; S1, stale/UNKNOWN boundary and fresh rebootstrap; C1, no-op escalation with mode-boundary cost. Enumerate and report every prefix, schedule, predicate violation, terminal effect, and cost for all three policies. These five rows are constructed discriminators, not sampled task data.
- **D:** `METHOD_PASS_SCOPED` only if a separate raw-only auditor reconstructs all schedules, finds the benign and harmful divergence witnesses, preserves the unsafe-prefix counterexample with equal terminal effect, verifies stale rebootstrap, and confirms lower B1 boundary cost for hysteresis. Any raw/schema/schedule mismatch is STOP; any unobserved false-safe or missed declared hard predicate is FAIL. A PASS establishes only fixture/oracle distinguishability.
- **C:** Exact mode equality remains preferable if a trustworthy effect/authority oracle cannot be specified. Scheduler/backpressure could reduce interruption cost without mode divergence.
- **U:** The planted fixture cannot estimate how often either divergence occurs, calibrate confidence/risk, establish GUI/action authority semantics, or support latency/token/task benefit claims.

## Provenance and execution gate

Scientific parent: [Issue #5352](https://github.com/Unjuno/agent-interface/issues/5352), clarification [comment #5944191631](https://github.com/Unjuno/agent-interface/issues/5352#issuecomment-5944191631). Original T0 in merged PR #5376 remains `FAIL_SAFETY_OR_REFERENCE_GATE` (fixed hysteresis 14/155 and minimum dwell 54/155 final-mode mismatches). It is neither modified nor rescored here. This T15 fixture uses five explicit symbolic traces and a new oracle; it does not claim to reanalyze the original 155 traces.

Before formal work: verify current main and source/input SHA-256, unique output/allocation, explicit non-overlapping WSLc CPU assignment, shared-runtime owner release, and current WSLc resource/network state; freeze exact cached image digest/platform and bounded commands. Candidate once; a separate raw-only auditor once only after candidate exit 0; no retry. On any failed gate, record STOP without claiming a scientific result.

Current execution disposition: **HOLD — no #5352-specific CPU/WSLc assignment is present.** The construction unit suite is host-only and is not a substitute for the planned isolated WSLc candidate/auditor pair.