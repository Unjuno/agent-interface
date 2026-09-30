# Issue #5278 — elastic verifier capacity synthetic T0 (v3)

Allocation: elastic-verifier-capacity-5278-t0-20260930-03.
Exact main parent: 28eabb92690b4a67243cb3ef8df439ae6595061d.
Branch: research/elastic-verifier-capacity-5278-t0-v3-20260930.
Additive path: research/verification/elastic_capacity_5278_t0_v3/.

v1's test import mismatch and v2's pre-run main-drift STOP are preserved unchanged in their prior branches and Issue comments. This is a fresh additive allocation, with corrected import and exact main ancestry. No formal invocation occurred in v1/v2/v3 before this freeze.

## H / T / D / C / U

**H.** With max four worker slots, deadline/freshness-aware elastic capacity improves usable-before-deadline results over fixed one-worker capacity during bursts, while using materially less idle worker-ms than fixed four and preserving identical verifier semantics.

**T.** Deterministic host-only CPython 3.11.9 simulation; no Docker, external service, GUI, model or GPU. Seven directed workloads / 51 fixed jobs: steady low, short burst, sustained burst, stale-version burst, startup-too-late, mixed mandatory/optional, scale-in while a job remains active. Policies: FIXED_SMALL=1, FIXED_LARGE=4, ELASTIC_DEADLINE_FRESHNESS_AWARE=1..4. Startup=300ms, teardown=150ms, idle retirement=600ms, tick=1ms, cap=4. Identical input bytes and synthetic verifier across arms; no randomness/tuning.

**D.** PASS_ELASTIC_CAPACITY_T0_SCOPED only if elastic short-burst completion > FIXED_SMALL; summed elastic idle worker-ms in short+sustained <=75% FIXED_LARGE; peak<=4; semantic digests equal across policies; no stale work completes; missing mandatory evidence never yields PASS; independent raw audit errors=0 and all five corruption controls reject. Partial endpoints are scoped HOLD/FAIL; provenance/audit mismatch is STOP. No T1 permission.

**C.** Directed synthetic schedules, priority/admission, optimistic feasibility estimate, discrete tick and fixed costs may favor/disfavor elasticity. A resident worker or batching may be simpler. No actual contention, physical memory, energy or service-time variability.

**U.** One synthetic finite T0. No real verifier/model/hardware benchmark, live workload, production scheduler, Orchestra integration, action authority, or general autoscaling claim.

The v1 auditor implementation was named audit.py while its tests imported auditor; the immutable failure STOP is at the v1 branch/evidence path. v3 changes only the test import to the actual audit module. simulator.py is candidate; audit.py is independent and imports no candidate code; workloads.json freezes all jobs; test_model.py is construction-only.

Construction command: python -m unittest discover -s scratch-5278-v3 -p test_model.py -v (CPython 3.11.9), exit 0, 8/8. Full transcript: CONSTRUCTION.txt.

Before formal execution, freeze exact GitHub blobs, local materialized source SHA-256, interpreter, command, raw path and collision check in an Issue comment. Exactly one local Python simulator invocation to an absent raw path; on exit 0 only, one separate raw-only audit and five in-memory corruptions. No retries, tuning, alternate paths or inputs. Host-only T0 uses no shared Docker slot and does not grant #5139's RTX lane.