# Issue #6619 — action-bound visual residual T0

## Disposition

`STOP_AUDIT_MUTATION_CONTROL_DEFECT`. The pinned WSLc candidate and auditor each ran once (exit 0; retries 0). The auditor's initial frozen execution reported exact reconstruction for 12 rows and `METHOD_PASS_SCOPED`, but its five corruption controls were only checked for inequality against the original object, not independently re-audited. That is not evidence that corruptions are detected. A post-run diagnostic correction used recursive calls to the full verifier, making the construction check unacceptably slow; it was not rerun formally. Therefore the reported method PASS is invalidated as an audit result; no efficacy conclusion is promoted. The hypothesis remains unresolved / no incremental benefit demonstrated.

## H / T / D / C / U

- **H:** Binding a conservative residual to actual delivered pan may improve deadline event detection at equal alarm budget without losing critical cues. The finite held-out fixture did not distinguish this from raw difference: both detected the single declared held-out flash.
- **T:** Frozen 12-row, 32x24 synthetic raster fixture, four arms, four-cell alarm budget, two-frame deadline. Full cases and protocol are in `PREREGISTRATION.md` and `cases.json`.
- **D:** Intended method gate required five genuinely rejected corruption controls. This gate is **not met** because the implementation's mutation-control result did not demonstrate independent rejection. No `METHOD_PASS_SCOPED` claim. Formal attempt was not repeated.
- **C:** The observed safe-arm counters were equal on the held-out cue; action binding did not show an incremental advantage under this fixture. Alarm selection used a deterministic high-contrast ranking.
- **U:** No natural image, live input, GUI/game, model, event prevalence, real deadline, safety, or product claim. Synthetic cue visibility and receipt correctness are stipulated.

## Frozen execution and artifacts

- Base commit: `87d5699db`; WSLc 3.0.1.0, kernel 6.18.40.1-1.
- Image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, Linux/amd64, image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`.
- Network disabled; pinned local image; one CPU and 512M requested. WSLc's run output did not include a cgroup warning in the captured stdout; no independent enforcement claim is made.
- Candidate and auditor each invoked once, exit 0. Candidate produced 12 rows. Initial auditor output listed 10 visible cues, 2 visible critical cues, and 5/5 nominal mutation rejections; the mutation number is invalidated for the reason above. Held-out action-bound and raw arms both detected the cue.
- Captured commands/stdout, raw and audit output, freeze and checksums are in `formal_01_20261002/`. Raw SHA-256 `4dd44921772817fdf2f27099ee4ca7c4d0971f90729cceb86d2612aaef2cd4c5`; initial audit SHA-256 `8f42bd599d538d469e878fe2cb9986d36bff117423fa72e2df4af814bdcb65ca`. Container IDs: candidate `b17f0bd409e1`, auditor `03b720cc2e49`; both exited 0. No shared container was stopped or modified.
- Construction tests before the formal run passed 4/4. Subsequent diagnostic tests found the mutation verification path unacceptably slow and were not counted as formal evidence. No retry, threshold adjustment, or result rewrite was performed.

## Next scientific step

Preserve this attempt. A distinct successor should redesign the auditor's mutation harness to invoke a bounded, non-recursive core oracle; make alarm-choice reconstruction exact (not budget-only); and predeclare enough held-out cases to compare incremental event retention under identical alarm budgets. No T1 or live allocation follows automatically.
