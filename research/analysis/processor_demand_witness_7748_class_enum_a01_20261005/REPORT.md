# Issue #8061 — result

**Disposition: `PASS_CLASS_BOUNDARY_SCOPED`.** The strict successor held every unknown or malformed class before calculating control-only demand, while its two recognized-class fixtures retained the expected finite results. One candidate invocation and one separate raw-only audit invocation both exited 0; retries were 0. The audit independently reconstructed all seven rows and returned zero errors.

## The observed predecessor boundary defect

The #7748 predecessor auditor filters control work with `job["class"] == "control"` but does not reject values outside its implied `{control, best_effort}` enum. On the frozen canary containing one `safety_critical` job (release 0, execution 2, deadline 1), the predecessor's read-only classifier returned `ELIGIBLE`; its `control_demand.feasible` was `true` because the unknown-labelled job vanished from the control subset, while `all_demand.feasible` was `false`. This is an invalid schema classification, not evidence that the unknown class should be scheduled as control. The strict successor returns `HOLD_UNKNOWN_JOB_CLASS` for that row.

## Frozen seven-case result

| Case | Candidate disposition | Control workload | All jobs |
|---|---|---:|---:|
| Recognized control + best-effort, feasible | `ELIGIBLE` | feasible | feasible |
| Control feasible, best-effort makes joint demand infeasible | `ELIGIBLE` | feasible | infeasible |
| Unknown `safety_critical` overload | `HOLD_UNKNOWN_JOB_CLASS` | not evaluated | not evaluated |
| Near-miss `contorl` | `HOLD_UNKNOWN_JOB_CLASS` | not evaluated | not evaluated |
| Missing class | `HOLD_UNKNOWN_JOB_CLASS` | not evaluated | not evaluated |
| Null class | `HOLD_UNKNOWN_JOB_CLASS` | not evaluated | not evaluated |
| Non-string class | `HOLD_UNKNOWN_JOB_CLASS` | not evaluated | not evaluated |

The raw-only auditor uses interval-demand witnesses and a separately implemented exhaustive slot-state search. For each eligible case the two independent feasibility reconstructions agreed. It rejected construction mutations for (a) an `ELIGIBLE` result attached to the unknown-class overload, (b) class substitution after the candidate, and (c) an omitted row. These mutation controls were pre-freeze construction tests; they did not alter the one formal raw result.

## Evidence and execution

- Frozen main: `3239217f54c199b582924ee69c7c80402f418a63`; exact sources and predecessor hashes are in `FREEZE.json`.
- Construction suite before freeze: 6/6 passed.
- Candidate raw SHA-256: `d20c8d7a62b583f1fd4da43e44783c98092a7f58089bae9202d3ab222c11dec0`.
- Independent audit SHA-256: `ed92c33f8450499cac21f13f4f104cba5388ce29a74ec92a9528aea5cb3a3dc9`.
- OrbStack's pinned no-network preflight stopped before Python startup (`crun: bpf create: Operation not permitted`). The preregistered host-only CPython 3.14.5 fallback was used; no isolation or resource-enforcement result is claimed. Exact image and config digests are in `ENVIRONMENT.json`.
- main advanced during preparation. The complete path sets were checked against the frozen source, issue and goal paths, recorded before formal calls in Issue #8061, and summarized in `MAIN_ADVANCEMENT.md`. The experimental source/input remained frozen; only the shared analysis index requires reconciliation for PR delivery.

## Claim ceiling

This is a seven-row parser/auditor boundary result in a deterministic finite model. It does not establish arbitrary finite scheduling feasibility, full CBS behavior, a runtime policy, an Agent Interface resource correspondence, host or container timing, GUI behavior, safety, or physical key release. Candidate and auditor were separately implemented by one author; this is not independent human review. Preserve #7748/PR #7762 and #7778 outcomes unchanged.
