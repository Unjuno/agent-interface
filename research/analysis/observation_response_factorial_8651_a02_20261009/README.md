# Issue #8651 A02 — observation × response factorial

## Successor relationship

A02 is a new immutable allocation after A01's operational STOP. A01's candidate failed before writing any row because its read-only container could not write to a host-mounted temporary output directory. A01's logs and Docker metadata remain unchanged at [the A01 first-outcome path](../observation_response_factorial_8651_a01_20261009/results/first-outcome/). A02 does not retry or replace that outcome.

## H / T / D / C / U

- **H:** In `deadline_transient_cue`, the active-minus-sham persisted-effect contrast under reactive response differs from fixed replay by at least 0.50; both controls have absolute interaction at most 0.10.
- **T:** 24 matched seeds across three regimes; 4 cells per seed (96 rows), deterministic balanced randomized order, fresh reset per seed/cell. Candidate and independent raw-only auditor run separately in the pinned Docker image. Four mutation controls test dropped row, swapped cell label, forged persisted effect, and observation arriving after its decision.
- **D:** `PASS_METHOD_SCOPED` requires ledger/timing/effect checks plus rejection of all four corruptions. `INTERACTION_SUPPORTED_SCOPED` additionally requires the preregistered contrast/control gates.
- **C:** Out-of-band or negligible observation cost; evidence-invariant response; or direct observation perturbation without interaction can yield no interaction.
- **U:** Synthetic deterministic schedule only. No claims about GUI/OS scheduling, models, safety, mediation, or user tempo.

## Execution and retention

The exact branch-create event runs the frozen source once. Candidate and auditor containers have no network, read-only filesystems, and CPU/memory limits; results are streamed over stdout into runner-owned files, avoiding writable host mounts. First outcome files (including failures and STOP metadata) are committed to `results/first-outcome/`. No retries or overwrites; changed source requires a new successor allocation.
