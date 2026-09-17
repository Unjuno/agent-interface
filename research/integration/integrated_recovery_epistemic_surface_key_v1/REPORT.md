# Integrated recovery epistemic surface key v1

Issue #881. Direct successor to #875's retained `HOLD_PREDECESSOR_IDENTITY_INCOMPLETE`.

## First formal outcome

Decision: **PASS_TYPED_RECOVERY_IDENTITY_SCOPED**.

The exact retained #855 and #864 archives were reconstructed byte-for-byte in a disposable container and matched the predecessor SHA-256/byte counts. The source-first freeze was published before any scored row. The formal runner was invoked exactly once, generated 32 retained-evidence rows, and was not rerun.

- stale source receipts: **16/16 `MISMATCH`**;
- fresh #864 receipts: **8/8 `EXACT_MATCH`**;
- fresh #855 receipts: **8/8 `CORE_MATCH_REFINEMENT_UNKNOWN`**;
- fabricated null: **0**; UNKNOWN-to-null/value coercion: **0**;
- observation-only fields remained `authority=none`, `task_input_granted=false`, `action_admission_eligible=false` **32/32**;
- frozen independent audit: PASS; copied-evidence corruption controls: PASS; preregistered missing/forged backend/client, known transient mismatch, and authority-escalation controls: PASS.

Representative semantics preserve the evidence difference instead of laundering it: #855 fresh/current has equal top-level client `6291468` but `transient_for=UNKNOWN` on both sides, so it is not promoted to exact identity. #864 fresh/current has client `10486269` with an explicitly observed `transient_for=10485768`, so it is exact. Stale receipts in both cohorts differ in top-level client identity and reject before any missing refinement can create compatibility.

## Interpretation

This repairs the integration *representation* boundary exposed by #875: incomplete predecessor identity can remain useful as typed recovery context without pretending absent data was observed. It does **not** prove that `CORE_MATCH_REFINEMENT_UNKNOWN` is sufficient for action admission. This experiment grants no authority and deliberately leaves such a promotion untested.

The result is narrow. Both retained cohorts happen to expose distinct X11 top-level client IDs across the stale transition. It does not cover XID reuse, process/session reincarnation, same-client modal changes with missing `transient_for`, semantic target identity, cross-platform recovery, live corrected-action success, token benefit, or latency benefit.

## Evidence

- rows SHA-256 `04643cdf5244d041b8ad6a56386c2d8d616fbedf7293a1e3adac39fda3126f4a`;
- RESULT SHA-256 `4c97698f174516f141889f2bca41b0f65f75891484bde1ca959be5bb288fbeb8`;
- AUDIT SHA-256 `dcf0122f1ea4b15968ab68f868fa23c43c0254d812aecd4023f628edb968b030`;
- formal invocation 1; formal reruns 0.
