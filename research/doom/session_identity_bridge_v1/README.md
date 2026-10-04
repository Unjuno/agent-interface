# V16 session identity bridge for MAP01 event records

## Question and scope

**H — Hypothesis.** In a V16 MAP01 run, one generated `run_id` can be joined to scorer updates, owner lifecycle records, and central V12 events without changing the event rows delivered to the controller. This is a source-composition claim only; it does not establish event authenticity, a live session, or task effect.

**T — Test.** Bind V16's generated run ID through a temporary environment variable while V12 runs. Preserve the existing `events.jsonl`, `delivered.jsonl`, and stdout serialization. Write an opt-in private `session-bound-events.jsonl` sidecar with the session ID, one-based source-event ordinal, and SHA-256 of the exact serialized source line. Bind the same ID to private owner-event records and V16 scorer sidecar rows. Verify helper behavior, identity restoration on success and failure, and the affected scorer/V15/V16 regression suites.

**D — Decision.** PASS for construction if the opt-in sidecar links to the unchanged serialized row, conflicting identities and malformed ordinals fail closed, and all focused regression tests pass. FAIL on any controller-visible row change or regression failure. HOLD for live attribution, causation, recovery, or game-effect conclusions without raw live evidence.

**C — Counterexamples and alternatives.** A caller can supply an unauthenticated environment value outside the V16 wrapper; therefore the optional V12 mode alone is not proof of identity. A sidecar can be incomplete after process or disk failure. Hash linkage detects mismatched lines but does not authenticate the producer. No timestamps or event ordering across independent clocks are asserted.

**U — Limits.** No VizDoom run, model, GUI, physical input, or container experiment was performed. The environment here lacks the `vizdoom` Python module, so V12 was syntax-checked but not imported or executed. The source event stream is unchanged by construction, but end-to-end controller neutrality and live session attribution remain unverified.

## Verification record

On 2026-10-04, these local commands passed:

- `cd research/doom && python -B -m unittest -v test_session_identity_v1` — 11/11
- `cd research/doom && python -B -m unittest test_acknowledged_scorer_v1` — 11/11
- `cd research/doom && python -B -m unittest test_session_map01_v15` — 8/8
- `cd research/doom && python -B -m unittest test_session_map01_v16_finalization` — 5/5
- `python -B -m py_compile research/doom/session_identity_v1.py research/doom/session_map01_v12.py research/doom/session_map01_v16.py research/doom/test_session_identity_v1.py` and `git diff --check` — PASS

The focused tests are local construction/regression checks, not independent live-run evidence. Related synthetic scorer-envelope work exists in draft PR #7544; this change addresses the separate missing runtime wiring in V12/V16 and does not replace that attribution analysis.
