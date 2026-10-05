# A02 result — PASS_METHOD_SCOPED

Allocation `CIRCUIT-REJECTION-COST-5375-A02-20261004-01`, registered before the formal runs in Issue #5375 comment 5975869308. Current-main base was `13bab54ea6d91978247ecc1b70e5060db752367a`. A01 remains a separate retained candidate-method failure plus auditor output STOP; it was not changed or rerun.

## Result

One WSLc candidate invocation exited 0 and emitted 10 rows. A separately invoked raw-only auditor exited 0, reconstructed all 10 rows, reported `errors=[]`, passed all seven scientific gates and rejected four of four copied mutations. The outcome is `PASS_METHOD_SCOPED` under the frozen synthetic fixture.

| Fixed case | Backend breaker | Upstream limiter | Reserved safety lane |
|---|---:|---:|---:|
| Nonzero rejection-cost storm: safety served | 0 | 1 | 1 |
| Nonzero storm: total charged cost / 19 | 19 | 15 | 17 |
| Zero rejection-cost control: safety served | 1 | 1 | 1 |
| Bounded-load control: safety served | 1 | 1 | 1 |

In the storm, backend-only spent its capacity on ingress, parse and one refusal/quarantine; it deferred seven requests and did not serve the mandatory safety check. Upstream admission charged work for all eight offers, completed two, carried six forward and served safety. The reserved-lane comparator also served safety while carrying all eight as unresolved. The fault-control row deliberately marks one obligation dropped, is explicitly ineligible, and was detected/excluded; no authority admission occurred.

## Provenance and limits

WSLc 3.0.1.0; cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14, pull never, network none, CPU=1. Source mounted read-only. Candidate raw and auditor receipt used distinct output directories; the audit input was read-only. Container inventories were empty immediately before candidate and auditor invocations and after completion. Captured output showed no cgroup/swap warning; no memory-enforcement claim is made.

Raw JSONL: 3,053 bytes, SHA-256 `131b83d140bdd7692554c8ef56657d2b3039c0e87f951ef50d275114680e6aa3`. Audit JSON SHA-256 `6d8406fc934fceb3bc6e8cde48828ffd5ee495db01bfc040bf6256c80ef50515`. The exact source identities are in `FREEZE.json`.

This is a hand-authored one-tick resource model with stipulated integer costs and a single fixture per stratum. It demonstrates only that this particular model distinguishes backend rejection cost from upstream admission and reserved-lane controls. It establishes no empirical Agent Interface cost, natural prevalence, multi-tick backlog recovery, runtime resilience, real safety or authority, live GUI/model effect, latency, performance, or product benefit. In particular, the reserved lane is already an alternative explanation for preserving the mandatory check; this result does not establish that upstream limiting is uniquely needed.
