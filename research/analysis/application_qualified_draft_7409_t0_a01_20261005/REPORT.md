# Issue #7409 T0 A01 result

## Result

Disposition: **`METHOD_PASS_SCOPED`** for the authored deterministic fixture. The frozen candidate ran once and the independent raw-only auditor ran once, both in OrbStack containers with exit code 0; retries: 0. The auditor reconstructed all 6/6 rows with no errors and rejected 6/6 frozen output mutations.

The direct shared-live comparator silently overwrote the human's same-field title in C2 and combined a changed formula with the human's new source value in C3. The staged path held both cases without promoting the agent draft. It preserved both writers' disjoint edits in C1, and merged disjoint edits against a changed `r2` live revision in C4 only after checking revision state. C5 deliberately used a separate UI context with a shared autosave backend; staging was refused before draft creation. C6 included a notification side effect; staging was refused and the staged effect list remained empty.

| Fixture | Staged result | Agent promoted? | Audit implication |
|---|---|---:|---|
| C1 disjoint writes | `PROMOTED` | yes | Both human and agent fields survive |
| C2 same-field writes | `CONFLICT_HOLD` | no | Human value remains live |
| C3 hidden read/write dependency | `CONFLICT_HOLD` | no | Formula edit held when its source changed |
| C4 later live revision, disjoint writes | `PROMOTED` | yes | `r2` checked; merged artifact advances to `r3` |
| C5 isolated UI, shared backend | `REFUSED_ELIGIBILITY` | no | No draft created or staged write made |
| C6 external side effect present | `REFUSED_ELIGIBILITY` | no | No draft or staged side effect emitted |

The mutation checks changed the raw candidate output to simulate a premature live write, silent same-field overwrite, ignored hidden dependency, unchecked revision, acceptance of the shared backend, and a draft external effect. The auditor rejected every mutation.

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

Post-run archival verification passed 4/4 checks for frozen source hashes, raw-output hashes, the scoped audit gate and staged outcomes. Two local test commands initially used the wrong working directory; the errors and both corrected 4/4 runs are recorded in [`results/construction/post_run_verification.json`](results/construction/post_run_verification.json). Neither reran candidate or auditor.

The candidate saw only the six frozen case definitions. The auditor was a separate implementation that consumed the frozen cases and candidate raw JSON; it did not import the candidate. Both implementations and the oracle fixture were authored by the same worker, so this is not independent human review.

## Scope and next gate

This establishes only that a finite fixture can distinguish staged draft behavior from a direct shared-live patch under the declared model. It does not establish draft/revision semantics in any real app, reduced live-view or focus interference, human preference, safe real-app merging, correctness of hidden application metadata, a runtime feature, product effect, or safety. The Issue's higher-level T1 hypothesis remains **not evaluated** and requires a separately frozen disposable application with genuine app-native draft/revision semantics and separately governed consented or scripted concurrent edits.
