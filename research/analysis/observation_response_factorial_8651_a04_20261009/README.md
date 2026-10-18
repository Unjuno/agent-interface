# Issue #8651 A04 — observation × response factorial

## Successor relationship

A04 follows the append-only operational records for A01–A03 and does not retry them:
- A01: container output permissions prevented any row from being written.
- A02: candidate and auditor exited 0, but raw data was lost when `jq` exceeded the shell argument limit during retention.
- A03: source-hash gate stopped before Docker image pull or candidate invocation because the frozen hashes were incorrect.

A04 reuses the exact candidate and independent auditor already executed successfully in A02, and uses a new allocation identity. Before creating this branch (which triggers the formal run), the source bytes are fetched from the immutable candidate commit and all hashes are checked against the freeze record.

## H / T / D / C / U

- **H:** In `deadline_transient_cue`, the active-minus-sham persisted-effect contrast under reactive response differs from fixed replay by at least 0.50; stable/no-information control interactions are each at most 0.10 in magnitude.
- **T:** 24 matched seeds across three regimes; 4 cells per seed (96 rows), deterministic balanced randomized order, independent raw-only audit, four frozen mutation controls.
- **D:** `PASS_METHOD_SCOPED` requires complete ledger/timing/effect checks and rejection of all four corruptions. `INTERACTION_SUPPORTED_SCOPED` requires the positive contrast threshold and both control bounds.
- **C:** Out-of-band/negligible observation cost, evidence-invariant response, or only direct perturbation can yield no interaction.
- **U:** Synthetic deterministic schedule only; no GUI/OS, model, safety, mediation, or user-tempo inference.

## Execution and retention

A branch-create event runs the source once in pinned, network-disabled, read-only Docker containers with CPU/memory limits. Candidate and auditor output is streamed to runner files. A host-side Python uploader sends bounded JSON requests to the GitHub Git Data API; raw payload is never placed in shell arguments. The complete first outcome—including failures/STOP, raw rows, audit, source hashes, Docker identity—is committed append-only. No retry or overwrite is allowed.
