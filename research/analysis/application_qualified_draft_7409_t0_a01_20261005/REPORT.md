# Issue #7409 T0 A01 result

## Result

The original formal `audit.json` reports **`METHOD_PASS_SCOPED`** for this authored fixture. A post-run source/raw review found that the required revision-check criterion was self-asserted, so the final qualified disposition is **`HOLD_AUDIT_WEAKNESS`**; do not accept the recorded PASS as satisfying the T0 gate. The frozen candidate ran once and the raw-only auditor once, both in OrbStack containers with exit code 0; retries: 0. The original auditor reconstructed 6/6 rows and reported 6/6 mutations rejected. Its revision mutation, however, only checked that a boolean matched an expected boolean.

The direct shared-live comparator silently overwrote the human's same-field title in C2 and combined a changed formula with the human's new source value in C3. The staged output held both cases without promoting the agent draft. It preserved both writers' disjoint edits in C1 and reported a disjoint merge against `r2` in C4. Source review found no actual base/current revision comparison behind C4's `revision_checked=true` field, so the revision-validation claim is not established. C5 deliberately used a separate UI context with a shared autosave backend; staging was refused before draft creation. C6 included a notification side effect; staging was refused and the staged effect list remained empty.

| Fixture | Staged result | Agent promoted? | Audit implication |
|---|---|---:|---|
| C1 disjoint writes | `PROMOTED` | yes | Both human and agent fields survive |
| C2 same-field writes | `CONFLICT_HOLD` | no | Human value remains live |
| C3 hidden read/write dependency | `CONFLICT_HOLD` | no | Formula edit held when its source changed |
| C4 later live revision, disjoint writes | `PROMOTED` in raw output | yes in raw output | Reports `r3`, but no comparison receipt proves that `r2` was checked |
| C5 isolated UI, shared backend | `REFUSED_ELIGIBILITY` | no | No draft created or staged write made |
| C6 external side effect present | `REFUSED_ELIGIBILITY` | no | No draft or staged side effect emitted |

The original mutation checks changed raw output to simulate a premature live write, silent same-field overwrite, ignored hidden dependency, unchecked revision, acceptance of the shared backend, and a draft external effect. The raw auditor reports all six rejected. Post-run review found the revision mutation is insufficient: it flips only the `revision_checked` field, while both candidate and auditor hardcode that field as true. The original six mutation outcomes remain unchanged and are not accepted as proof of the revision check.

The post-run source/raw qualification is retained in [`results/post_run_review/REVIEW_QUALIFICATION.md`](results/post_run_review/REVIEW_QUALIFICATION.md). It does not modify or rerun the frozen candidate, auditor, or raw outputs.

## Execution and provenance

- Issue: https://github.com/Unjuno/agent-interface/issues/7409
- Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A01-20261005-01`
- Freeze commit: `5a258dc1ef6ed72d8564e81579b88056702d5844`; frozen main base: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`.
- Remote main at candidate invocation: `38fe303fec59cde15f708483cae00bf617f3bdd0` (one unrelated #8112 A06 commit advanced after freeze; Issue #7409 still had no allocation comment or matching branch/PR at the pre-invocation check). The frozen experiment had no exact-main gate; no source or input bytes changed.
- Image: `python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`, Linux arm64. OrbStack server 29.4.0; Docker client 29.5.2.
- Runtime requests: `--network none`, one CPU, read-only root filesystem and source mount, distinct writable output mount, 16 MiB no-exec tmpfs at `/tmp`. These are requested settings; CPU/cgroup enforcement was not independently measured.
- Docker reported cgroup v2 and warning `DOCKER_INSECURE_NO_IPTABLES_RAW is set`. Swap behavior was not assessed.
- Mount preflight read the source, observed source-write rejection, and wrote/read a distinct output artifact. This was not a candidate or auditor invocation.
- A post-run `docker ps` snapshot showed no running containers after the `--rm` candidate and auditor invocations.
- Candidate raw SHA-256: `ae6ca2cbbfe6d5669f0dd8de8665b224cf100344ae991575fe3f7f66dc43279d`.
- Auditor raw SHA-256: `9b74747dad9938159f76d7139ebcdc5c760173b389f724f33ce339839e2547eb`.
- Frozen source and input SHA-256 values are in [`frozen/FREEZE.json`](frozen/FREEZE.json) and [`frozen/SHA256SUMS`](frozen/SHA256SUMS). Exact invocation commands, exit codes, stdout/stderr hashes and run counts are in [`results/a01/run_metadata.json`](results/a01/run_metadata.json).

Post-run archival verification passed 4/4 checks for frozen source hashes, raw-output hashes, the original audit record, and its qualification. Two local test commands initially used the wrong working directory; the errors and both corrected 4/4 runs are recorded in [`results/construction/post_run_verification.json`](results/construction/post_run_verification.json). Neither reran candidate or auditor.

The candidate saw only the six frozen case definitions. The auditor was a separate implementation that consumed the frozen cases and candidate raw JSON; it did not import the candidate. Both implementations and the oracle fixture were authored by the same worker, so this is not independent human review.

## Scope and next gate

The retained output supports only the listed finite field-conflict/refusal observations; because the revision-check gate is not evidenced, the overall T0 method PASS is **not accepted**. Nothing here establishes draft/revision semantics in a real app, reduced live-view or focus interference, human preference, safe real-app merging, correctness of hidden application metadata, a runtime feature, product effect, or safety. The Issue's higher-level T1 hypothesis remains **not evaluated** and requires a separate allocation with genuine app-native draft/revision semantics and separately governed concurrent edits. The consumed A01 is not to be rerun.
