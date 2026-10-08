# Issue #6593 — user-relative benefit method T0

Allocation `USER-RELATIVE-AGENCY-BENEFIT-6593-T0-20261002-01`
Status: `PASS_METHOD_SCOPED` for synthetic schema/accounting only.
Frozen base: `4a577c1bbb57c055bb489e57f513f8672126fe27`.
Runtime: host-local CPython 3.14.5 on macOS. All inputs are authored synthetic values; no human/AT user data, participant contact, GUI, model, network collection, or external effects.

## Result

Construction tests passed 6/6. After freeze, candidate and independent raw-only auditor each ran once, with zero retries. Candidate exited 0 and emitted 7 cases / 13 assigned matched pairs. Auditor exited 0, independently reconstructed all cases and pairs, and returned `errors: []`.

In the stipulated reversal fixture, pooled standardized-agent minus human time is +10s (agent slower), while the one synthetic participant's matched assisted-offer minus unaided time is -10s on two independently verified pairs. The same-direction fixture returns -10s on both contrasts and is not called a reversal. Five control cases remain HOLD: fast wrong effect, offer refusal, missing outcome, changed AT configuration, and only one verified matched pair. Both refused offers remain in the assignment denominator. Agency ratings are preserved as a separate field and are not traded against correctness or time. Seven corruption controls are rejected.

## Interpretation boundary

This establishes only that a finite accounting implementation can represent and distinguish the stipulated pooled-versus-within direction reversal while retaining all assignments, refusal, hard effect correctness, configuration identity, agency ratings and insufficient evidence. It does not establish participant benefit, accessibility, AT compatibility, causal effects, population direction, preferred pace, burden reduction, or any human/agent performance claim. No T1 human study is authorized or proposed by this result.

## Reproduction and retained evidence

Run `python3 -m unittest -v test_benefit.py` for the six construction tests. Frozen source/fixture/test hashes are in `FREEZE.json`. Candidate and auditor stdout/stderr, raw JSON and audit JSON are retained in this directory. SHA256SUMS covers all frozen inputs and formal outputs.
