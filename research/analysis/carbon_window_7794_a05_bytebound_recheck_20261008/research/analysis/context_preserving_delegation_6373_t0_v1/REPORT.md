# Issue #6373 — context-preserving delegation T0

**Disposition: `PASS_METHOD_SCOPED` for the finite synthetic method only.** Across eight deterministic histories, footprint-gated RESTORE_PLUS_DIFF preserved all stipulated intended effects, external changes, required artifacts, and unresolved state, while reducing modeled next-task context mismatches relative to SUMMARY_ONLY. It must not be read as human or GUI evidence.

## H/T/D/C/U

- **H:** Gated restoration plus residual diff can reduce next-task context mismatch while preserving intended/external state, unlike blind restoration.
- **T:** Eight fixture histories × NO_RESTORE, SUMMARY_ONLY, RESTORE_ONLY, RESTORE_PLUS_DIFF = 32 rows; independent raw-state reconstruction and a successor audit-only recomputation of next-task success.
- **D:** Pass only if RESTORE_PLUS_DIFF preserves all effects, external fields, artifacts and unresolved state, reports exact residuals, and has no worse fixed next-task success than SUMMARY_ONLY. This test met those finite conditions.
- **C:** A summary may suffice; restoration may be coupled, stale, destructive, or overconfident.
- **U:** Fully scripted states and next-task requirements. No actual GUI, callbacks, people, latency, or end-to-end benefit measured.

## Result

| Policy | Fixed next-task fixtures with zero required-context mismatches | Total modeled context mismatches | Safety observations |
|---|---:|---:|---|
| NO_RESTORE | 3/8 | 9 | No restoration hazards; leaves navigation context changed |
| SUMMARY_ONLY | 3/8 | 9 | Same state as NO_RESTORE, with exact diff |
| RESTORE_ONLY | 6/8 | 3 | Destructive in 4 fixtures: autosave erased B20, stale viewport overwrite, required download deletion, and false clearing of unknown modal/held input |
| RESTORE_PLUS_DIFF | 5/8 | 4 | Preserved all intended effects, external changes, required artifacts, unknowns, and exact residual differences |

Success here means the returned fixture state exactly meets its predeclared `next_requires`; it is not task performance by an agent or human. The safety-aware policy has one fewer exact-context success than blind restore-only, but avoids four destructive/stale/false-safe outcomes and beats SUMMARY_ONLY on the declared proxy. Its conservative abstention in the autosave-coupled and unresolved-input cases is intentional.

## Allocation and audit history

- A01 ran the candidate once and its independent auditor once in separate OrbStack containers. The first audit verified all rows and policy safety fields but omitted the preregistered per-case downstream-success comparison; therefore A01 alone did not establish the full decision rule.
- A02 is a one-shot audit-only successor: candidate was not rerun. It independently recomputed all 32 mismatch counts and policy success totals from frozen raw/candidate/oracle bytes; all rows valid, all RESTORE_PLUS_DIFF invariants hold, and the summary comparison passes. Four audit corruption controls passed construction before freeze. Two construction failures and their fixes are in A02 `BUILD_HISTORY.md`.

The candidate and audits used OrbStack `python:3.12-slim`, pinned local image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, no network, read-only root/input, 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped and no-new-privileges. Reproduction entrypoints: `RUN.sh` under the A01 and A02 directories. Portable SHA256 manifests accompany every allocation.

No runtime restoration mechanism, consent, authority, or production behavior is proposed or changed. A human task-chain study or live application test would require a separately authorized successor.
