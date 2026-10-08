# Issue #8651 A03 — observation × response factorial

## Successor relationship

A03 follows two retained operational failures and leaves them unchanged:
- A01 stopped before output because the container could not write to a host bind-mounted output path.
- A02 candidate and auditor each returned exit code 0, but final evidence retention failed when `jq` passed the large base64 raw ledger as a command-line argument. Raw and detailed audit files were lost with the ephemeral runner; no formal contrast is asserted for A02.

These records remain in the A01 and A02 allocation paths and on Issue #8651. A03 does not rerun either allocation. It is a new, hash-frozen allocation with the same finite protocol and a streaming Git Data API evidence uploader.

## H / T / D / C / U

- **H:** In `deadline_transient_cue`, the active-minus-sham persisted-effect contrast under reactive response differs from fixed replay by at least 0.50; both controls have absolute interaction at most 0.10.
- **T:** 24 matched seeds across three regimes; 4 cells per seed (96 rows), deterministic balanced randomized order, fresh reset per seed/cell. Candidate and independent raw-only auditor run in separate pinned Docker containers. Four mutation controls cover a dropped row, swapped cell label, forged effect, and observation arriving after its decision.
- **D:** `PASS_METHOD_SCOPED` requires full ledger/timing/effect checks and rejection of all four corruptions. `INTERACTION_SUPPORTED_SCOPED` additionally requires the preregistered contrast/control gates.
- **C:** Out-of-band or negligible observation cost; evidence-invariant response; or direct observation perturbation without interaction can yield no interaction.
- **U:** Synthetic deterministic schedule only. No claims about GUI/OS scheduling, models, safety, mediation, or user tempo.

## Execution and retention

The exact branch-create event runs the frozen source once. The Docker containers have no network, read-only filesystems, and CPU/memory limits, with outputs streamed to runner-owned files. The host uploader uses Python's HTTP client and streams JSON request bodies to GitHub's Git Data API (no shell argument carries raw data). Raw ledger, audit, run metadata, container identity, and hashes are committed as an append-only first outcome, including STOP/failure states. No retry or overwrite is allowed.
