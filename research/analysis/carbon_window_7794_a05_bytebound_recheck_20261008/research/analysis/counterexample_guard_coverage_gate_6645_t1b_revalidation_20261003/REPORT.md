# Issue #6645 T1b independent integration revalidation report

**Host result:** `PASS_INDEPENDENT_REVALIDATION`. One frozen Windows host read-only auditor invocation exited 0, no errors, 30 files verified, five rows reconstructed, three gate-delta rows. No candidate or container ran in this allocation.

**Distinct WSLc result:** `HOLD_SHARED_WSLc_ATTRIBUTION_AND_EXCLUSIVE_ALLOCATION_UNRESOLVED`. The proposed neutral-ID candidate and WSLc auditor remain 0/0, retries 0. No observed label-invariance or memory-relief result is claimed. The parent T1b allocation, raw outcomes, and all 30 files are unchanged.

## Independent retained-record reconstruction

The host CLI ran 2026-10-03 09:27:04.319209–09:27:04.644932 UTC using Windows Python 3.12.10, PID 27620. [AUDIT_FREEZE.json](AUDIT_FREEZE.json) precedes it. [Raw stdout](results/host_audit_01/stdout.txt), [stderr](results/host_audit_01/stderr.txt), and [attributed receipt](results/host_audit_01/receipt.json) retain the exact command, source hashes, times, disposition, and stream hashes.

| Frozen synthetic case | Oracle label | Gate disabled | Gate enabled |
| --- | --- | --- | --- |
| valid_complete_coverage | safe | ADMIT | ADMIT |
| known_stale_complete_coverage | harmful | REFUSE | REFUSE |
| hidden_modal_harmful_incomplete_coverage | harmful | ADMIT | UNKNOWN |
| hidden_modal_safe_incomplete_coverage | safe | ADMIT | UNKNOWN |
| unregistered_surface_family | unknown | ADMIT | UNKNOWN |

All ten decisions match an independent rule using fixture/contract data, without calling/importing the candidate or historical auditor. The hidden safe/harmful rows are identical except IDs and both lack modal coverage. Pinned decide() directly reads covered_predicates, observations, surface_family, not id. IDs nevertheless expose outcome words; no fresh neutral-ID candidate result exists.

The retained original candidate/auditor receipts record separate read-only, network-disabled, cap-drop-all containers, uid 65534:65534, exit 0, OOMKilled false and restart count 0. The candidate had only its candidate_input mount, not the oracle. This is a check of historical receipts and source identity, not a fresh runtime-isolation or memory-cap demonstration.

## Verifier evidence and limitations

Six pure tests pass with 23 effective corruptions rejected: 12 raw/schema/identity, three manifest, three boundary, four label-checker, one duplicate JSON key. [Run 02](results/verifier_controls_02/receipt.json) records the passing source. The label-checker success control is synthetic retained output, not candidate execution.

[Run 01](results/verifier_controls_01/receipt.json) failed because the construction effectiveness assertion used Python equality (True == 1). Its source snapshots and raw failure remain. Canonical JSON comparison repaired the effectiveness check. An unconditional count marker can print despite a failed unittest subtest; exit code/stderr are authoritative. No failed control is promoted to PASS based on stdout. [Review](REVIEW.md) notes this nonblocking reporting limitation; frozen sources/results are not retroactively changed.

Three earlier host construction suites each ran a candidate once, before this read-only revision, with no separately archived candidate raw. Those are development-only, not this allocation's scientific result; see [construction history](CONSTRUCTION.md).

## WSLc migration and STOP

The selected route is installed WSLc 3.0.1.0 without Docker Desktop. Two environment-only preflights before #5085 HOLD recognition exited 0: JSON input reading and a distinct output-marker write. Both executed no candidate; [commands and warning](results/PREFLIGHT.md) are retained. Relation to shared bridge state is unknown. No WSLc command followed HOLD recognition.

The observed cached image was python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f, local image ID sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4, linux/amd64, Python 3.12.14. Historical T1b was linux/arm64. Cache facts are an observation, not a lease or guarantee of future availability.

The prepared neutral-ID payload has exactly three candidate-visible inputs, no oracle/raw/report/repository mount. [PROPOSAL.json](pending_label_probe/PROPOSAL.json) gives hashes and an unexecuted command. Shared-state attribution and exact exclusive allocation are unresolved; [STOP.md](STOP.md) preserves the closeout. Future execution needs a fresh allocation, current attribution, and no overwrite/replay of this record.

WSLc warned: "Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap." Requested 128M configuration is not a hard-limit or memory-pressure-resolution finding. The final host audit and payload preparation invoke no shared runtime. The earlier preflights' shared-state effects remain unknown; no Docker Desktop/global WSL setting, shared image/volume, or other worker's process was intentionally changed.

## Scope

This is finite synthetic retained-data revalidation, not another T1b trial or a blinded prospective causal result. External family-registry completeness, oracle truth, unknown-unknown discovery, real skill/GUI safety, production tasks, utility, portability, latency and performance remain unestablished. Issue #6645 stays open. Evidence integration and WSLc launch disposition are independent: the verified host audit and STOP may be reviewed without running the pending candidate.
