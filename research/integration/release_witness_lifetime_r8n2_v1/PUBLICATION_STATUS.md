# r8n2 publication status — source retained, formal evidence unavailable

Issue #4345 reports `PASS_RELEASE_WITNESS_LIFETIME_SCOPED` for 16 first-run cases, 1,403 audit checks, 12/12 copied-evidence controls, and 10 policy tests. The report is preserved in the [Issue comment](https://github.com/Unjuno/agent-interface/issues/4345#issuecomment-5825679121); this repository path does not contain the raw sessions, launcher receipts, audit output, or control output needed to independently reproduce that formal result.

This path preserves the 12 hash-frozen source/environment/plan files from branch `research/release-witness-lifetime-3066-20260925-r8n2` at source-freeze commit `650202c62e4e62348da8b4fe06e87adf47b68a29`. Their FREEZE.json hashes were independently recomputed with zero mismatches. Python syntax compilation and the construction-only `test_policy.py` suite passed locally (10/10); these checks do not validate any formal session or reported audit result.

Disposition: `HOLD_PUBLICATION_INCOMPLETE`. Do not treat the Issue-reported PASS as independently verified, do not rerun or replace any of the consumed 16 cases, and do not infer physical HID release timing, full recipient-process death, or the parent #3066 guarantee. The source freeze is retained for inspection; raw evidence remains absent from this publication. Issue #4345 and parent #3066 remain open.
