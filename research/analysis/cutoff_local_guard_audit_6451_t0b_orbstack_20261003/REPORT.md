# Issue #6451 T0b report

## Disposition

**PASS_METHOD_SCOPED** — candidate and independent auditor each ran once in separate pinned OrbStack containers; both exited 0, OOM=false, retries=0. The raw file was durably captured before the auditor and mounted read-only for independent reconstruction. The auditor reconstructed all six cases and 72 rows, returned zero errors, and rejected all 5/5 effective corruption controls.

- Valid sharp cutoff: local-linear effect 2.0; symmetric within-bandwidth mean difference 11.0 (the latter retains the stipulated smooth age trend and is not the treatment effect).
- Smooth zero-effect control: local-linear effect 0.0; within-bandwidth mean difference 9.0. No guard gain is declared.
- Sorting/bunching, coincident app/focus transition, and timestamp heaping are refused with their preregistered reasons.
- Noncompliance: first-stage jump 0.5, outcome jump 1.0, fuzzy local effect 2.0.

Latest main `c2dc6e4fe2f5114418468cafbdd57deec0e4096e` was merged before allocation start (unrelated archived evidence only); all frozen source hashes remained unchanged. The full local Analysis Index suite passed 19 commands / 114 tests; T0b construction 5/5 and index 556 passed.

## H / T / D / C / U

See `PREREGISTRATION.md`. The predecessor allocation remains `STOP_RAW_OUTPUT_NOT_RETAINED`; candidate=1, auditor=0, retries=0. T0b is a new allocation with fresh raw output and no changes to its predecessor evidence. Raw candidate, separate audit receipt, both stage run records, stdout, exit codes, container configuration/state and SHA-256 manifests are retained under `results/` and `execution/`.

## Scope

Synthetic six-case method fixture only. No live GUI threshold, causal effect, safety, model behavior, user, or product claim.
