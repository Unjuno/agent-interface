# A07 v4 synthetic identity reconciliation

The v3 auditor counts admissions and explicit release transitions by key only. A synthetic matched cancellation with step/token mismatch produced scoped PASS. This v4 copy requires each `(step, key, intent_token)` identity to be well-formed, unique, and equal across the admission and explicit release rows. Malformed values are checked before hashing. Missing legacy identity remains FAIL rather than being guessed. The v4 output is named `AUDIT_V4.json`; v1–v3 sources and their saved outputs are unchanged.

A controlled synthetic test covers a valid match, wrong or malformed step/token, and duplicate identities. It failed on the copied v3 logic and passes with the v4 rule. The test module also runs the 16 historical v3 tests, for 19 total, under normal and optimized Python. No saved A07 data or historical audit was rerun.

This explicit-transition contract does not reconcile terminal owner cleanup when an explicit transition is missing; such cases fail closed in this auditor. It does not establish physical release, GUI task effect, live correctness, or formal pass. The other cleanup reconciliation is a separate evidence path and is not composed here.
