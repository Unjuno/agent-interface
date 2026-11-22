# Issue #7827 — per-artifact GUI macro translation validation T0

Allocation: `UNJUNO-7827-TV-A01-20261005-01`. Finite standard-library model only; no GUI, model, user-input, or runtime action.

## First outcome

Candidate exit 0: `PASS_TRANSLATION_VALIDATION_METHOD_SCOPED`. Independent auditor exit 0: `FAIL_METHOD`. All seven counterexamples replayed, but candidate `contexts_checked` disagrees with independently observed counts because it reports the full context-domain size after returning on the first counterexample. See `FIRST_RESULT.json`.

This is the first outcome; do not rerun this allocation. `SOURCE_PLAN.md` is byte-for-byte original. `FREEZE.json` supersedes its stale base/runtime header and pins the formal inputs.

## Raw capture custody

Exact stdout/stderr were emitted in the originating Codex tool result and were not written locally because C: had zero free bytes. This package carries an extracted disposition, not byte-exact streams. Preserve the originating thread's tool result before any successor allocation. No execution authority or resource-enforcement claim follows.
