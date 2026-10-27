# Issue #8651 A01 — observation × response factorial

## H / T / D / C / U

- **H:** In `deadline_transient_cue`, the active-minus-sham persisted-effect contrast under reactive response differs from fixed replay by at least 0.50; both controls have absolute interaction at most 0.10.
- **T:** 24 matched seeds across three declared regimes; 4 cells per seed (96 rows), deterministic balanced randomized order, fresh reset per seed/cell. Candidate and independent raw-only auditor run separately in the pinned Docker image. Four frozen mutation controls test dropped row, swapped cell label, forged persisted effect, and observation arriving after its decision.
- **D:** `PASS_METHOD_SCOPED` requires ledger/timing/effect checks plus rejection of all four corruptions. `INTERACTION_SUPPORTED_SCOPED` additionally requires the preregistered contrast/control gates.
- **C:** Out-of-band or negligible observation cost; evidence-invariant response; or direct observation perturbation without interaction can yield no interaction.
- **U:** Synthetic deterministic schedule only. No claims about GUI/OS scheduling, models, safety, mediation, or user tempo.

## Reproduction and evidence

The workflow runs only on creation of the exact allocation branch. It pins and verifies the source hashes and image, runs with network disabled and resource limits in two separate containers, and retains first outcome files under `results/first-outcome/` even on STOP/failure. Do not rerun or replace first-outcome evidence; use a successor allocation for protocol changes or retries. The README, protocol, candidate, auditor, freeze record, and workflow are additive and isolated from other research paths.
