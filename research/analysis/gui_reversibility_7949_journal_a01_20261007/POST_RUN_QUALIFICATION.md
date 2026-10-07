# Post-run qualification (A01)

The frozen fixture stores `agent_value="original"` before and after the complete disjoint external write, and the certificate stores `agent_original="original"`. The candidate's proposal therefore names the correct bounded field/value and preserves the external field, but applying it would not change the DB. This means the proposal's field-scope and revision-binding were exercised, while non-idempotent restoration of a previously changed agent field was not.

This was discovered by inspecting the immutable `cases.json`, candidate output, and retained `complete_disjoint.sqlite` after the one-shot stages. No source, input, raw output, audit output, or formal result was changed or rerun. Keep the frozen verdict as recorded; do not cite A01 as evidence that an actual changed value was restored. Any follow-up must use a fresh allocation and additive path with a distinct current agent value and certificate baseline, and must preserve all A01 files unchanged.
