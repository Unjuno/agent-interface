# Post-run qualification (duplicate execution)

The frozen fixture stores `agent_value="original"` before and after the complete disjoint external write, and the certificate stores `agent_original="original"`. The candidate's proposal therefore names the correct bounded field/value and preserves the external field, but applying it would not change the DB. This means the proposal's field-scope and revision-binding were exercised, while non-idempotent restoration of a previously changed agent field was not.

This no-op property was discovered by inspecting the immutable `cases.json`, candidate output, and retained `complete_disjoint.sqlite` after the duplicate stages. No raw output or audit output was rewritten. The top-level STOP is due to the more fundamental allocation collision; this no-op is an additional property of the duplicate fixture only. Any future work must use a fresh allocation and additive path, and preserve the original A01 files unchanged.
