# Construction history (not formal allocations)

This file separates harness development from preregistered evidence. Every
pilot below preceded formal-01 and is excluded from its sample and PASS gate.
Raw PNGs/JSON and STOP/HOLD notes are retained in the named subdirectories.

- `template_sweep_01`: XCalc UI was set to each integer 0–15 using XTEST and
  captured through the public observation API. The frozen `[198,5,37,27]`
  pixel-template adapter reconstructed 16/16 values with zero mismatches.
- `template_replay_01`: a fresh Xvfb/XCalc run displayed 8 and emitted the
  same complete PNG SHA-256 as the construction value-8 sample.
- `pilot_01_stop`: one public capture then STOP from passing unsupported
  `partial` keyword to the candidate; no candidate result was emitted.
- `pilot_02_stop`: 11 capture PNGs then STOP while serializing the intentional
  no-observation ambiguous-target row (`reply=None` dereference).
- `pilot_03_xid_reuse_hold`: runner emitted 13 rows/12 captures, but the
  independent audit first stopped on its own wrong expected prior state. Raw
  candidate output also showed XID `4194322` reused by replacement XCalc and
  incorrectly returned SUPPRESS under XID-only binding. This candidate finding
  was not reached by that audit and is exploratory/unaudited.
- `pilot_04_audit_hold`: runner complete; audit harness first required a
  candidate state after fail-open and then checked the wrong XID field. Its
  supplemental audit output passed after repair but overstated PREPARE's
  phase-support comparison; `AUDIT_REVIEW.txt` records that error.
- `pilot_05_audit_hold`: runner complete, initial auditor and control wrapper
  had defects/configuration mistakes. Follow-up on the unchanged runner output
  passed the corrected independent audit and three adversarial auditor
  corruption controls. It remains construction rehearsal, not formal evidence.

The XRes mechanism was tested before preregistration: in private Xvfb the same
XID/resource base was allocated to replacement XCalc with a distinct process
PID. Formal-01 binds display, XID, resource base, XRes local PID, and a caller
window generation, and verifies owner PID before/after each public capture.

Construction failures and intermediate reports remain immutable. They explain
why the formal candidate has process-instance binding and why the control
comparison and auditor now use separate independent calculations.
