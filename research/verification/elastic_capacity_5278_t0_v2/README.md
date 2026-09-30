# Issue #5278 — elastic verifier capacity, synthetic T0 (v2)

Allocation candidate: `elastic-verifier-capacity-5278-t0-20260930-02`.
Frozen main at branch creation: `972fd822dd75dba7def4d0601d6b96830903d184`.
New additive path: `research/verification/elastic_capacity_5278_t0_v2/`. The v1 preparation STOP remains immutable at `research/verification/elastic_capacity_5278_t0_v1/evidence/construction01/STOP.txt`; this is a new source/layout candidate, not a changed prior record.

## H / T / D / C / U

**H.** Under a fixed maximum of four worker slots, deadline/freshness-aware elastic capacity increases usable-before-deadline results over a one-worker fixed pool during bursts, while using materially less idle worker-ms than a four-worker fixed pool and preserving exactly the same verifier semantics.

**T.** Deterministic host-only Python 3.11.9 simulation; no Docker, external service, GUI, model or GPU. Seven directed finite workloads and 51 fixed jobs are in `workloads.json`: steady low load, short burst, sustained burst, stale-version burst, startup-too-late, mixed mandatory/optional and scale-in while another worker is active. Compare fixed-1, fixed-4 and elastic-1..4. Startup=300 ms, teardown=150 ms, idle retirement=600 ms, tick=1 ms, maximum=4. Identical payload/job bytes and one synthetic verifier/version in each arm. No randomness or parameter search.

**D.** `PASS_ELASTIC_CAPACITY_T0_SCOPED` requires: (1) elastic short-burst completed count > FIXED_SMALL; (2) summed elastic idle worker-ms in short+sustained bursts <=75% of FIXED_LARGE; (3) peak<=4; (4) semantic digest equality across all policies; (5) no stale completion and no PASS when mandatory evidence is incomplete; (6) an independent raw-only audit with zero errors and all five frozen corruption controls rejected. Partial endpoint success maps to a scoped HOLD/FAIL subtype; provenance/audit failure is STOP. No T1 authorization follows.

**C.** Directed synthetic schedules, a priority scheduler, optimistic feasibility estimate, millisecond tick and fixed service/startup costs may favor or disfavor elastic policy. A resident worker or batching may be simpler. No real contention, physical memory, energy, or runtime scaling is measured.

**U.** One synthetic finite T0 only. No real verifier, model/hardware benchmark, live workload, production scheduler, Orchestra integration, action authority or general autoscaling claim.

## Candidate and execution gates

`simulator.py` is the candidate; `audit.py` is independent and imports no candidate code. The construction suite now imports `audit` (the v1 test referenced nonexistent module `auditor`; preserve its STOP unchanged). Every formal input, source digest, Python executable/version, raw output path collision check and invocation count must be preregistered in a top-level Issue #5278 comment before formal execution. The exact source files must be fetched back from this branch and text-byte compared to local execution inputs.

Formal scope is one host-only invocation writing exclusively to a fresh collision-checked raw path, followed by one separate audit process. Zero retries/parameter changes after formal start. Construction/audit-complexity control runs are not formal. This synthetic lane uses no shared Docker/OrbStack slot; it does not grant or consume #5139's RTX lane.

Roadmap: current-main branch/path -> fetched source verification -> one construction suite -> preregistration comment -> exactly one raw T0 -> separate raw-only audit plus five corruptions -> preserve exact failure/PASS -> issue result -> additive Draft PR and exact-head CI/review. Stop after T0.
