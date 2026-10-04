# Preregistration — INFERENCE-DISTURBANCE-COUPLING-7470-T0-20261004-A03

- **H:** With periodic latency `[1,2,3,4]` and disturbance `[0,1,2,3]` sequences intact, relative circular phase changes the planted-interaction plant's peak/exposure; the null plant remains phase-invariant.
- **T:** Enumerate all four unique circular shifts of latency relative to the fixed disturbance sequence, in null and planted plants. Report every trajectory and realized phase pairing; independently reconstruct raw rows and reject changed-marginal, missing-shift, and changed-score mutations.
- **D:** `PASS_METHOD_SCOPED` only for exact intact circular shifts, invariant null outcomes, at least one phase-dependent planted outcome, full independent reconstruction, and all mutation controls rejected. Any mismatch is `FAIL_METHOD`.
- **C:** This is a small constructed periodic sequence and a planted interaction; cyclic autocorrelation preservation does not make it representative of live timing or disturbance processes.
- **U:** No prevalence, causality, runtime coupling, GUI/game, live safety, human benefit, or deployment threshold is established. The wraparound transition is part of this finite period; no seam is dropped.

Each input sequence is immutable as an ordered period; treatments are latency rotations only. Four unique rotations are tested. One candidate invocation, then one auditor invocation only after candidate exit 0; no retries. Fresh output directory must be absent. Candidate/auditor/spec/test hashes are pinned in PRELAUNCH_FREEZE.json before formal execution.
