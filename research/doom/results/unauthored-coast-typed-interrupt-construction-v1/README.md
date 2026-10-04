# Unauthored-coast typed-interrupt construction candidate v1

This additive package records a controller-boundary construction result for Issue #59. It does not alter retained v38/v39 controllers, traces, or allocations.

## H/T/D/C/U

- **Hypothesis:** During an input-free, unauthored coast, sustained bound health decline can make an in-flight model answer stale. Typed observations precede their matching screenshot rows, so a useful interrupt must wait for a current image before replanning.
- **Treatment:** Candidate v40 subscribes only the unauthored empty coast to early typed health events. Its exploratory rule is the saved-only candidate from Issue #59 comment #5977611388: with the last typed health at/before model start as baseline, signal after at least two of the latest three typed samples are each <= baseline-5. A trigger interrupts model/coast; verified-empty release stays mandatory; then use an already-drained matching/newer screenshot or wait for one. Unknown/expired/binding-invalid health still fails closed. Authored guards and fresh action admission are unchanged.
- **Decision:** Construction boundary passes: Python syntax compilation and 12 focused unit tests pass (9 monitor/handoff, 3 controller integration). Tests cover the two-of-three boundary, one-sample non-trigger, window aging, unknown health, authority non-escalation, authored-path preservation, release-before-return, and both screenshot ordering races.
- **Control:** Historical v39 source and allocation remain unchanged. Existing fresh final action admission remains the input-authority gate. Replay inputs: retained v38 report/events SHA-256 7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58 / 80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3; and v39 report/events 719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687 / 2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381. Existing saved-only comparison: rule fires in both v39 unauthored waits, not stable d0, and not the censored v38 prefixes; the v38 d2 prefix includes a six-point minimum loss without two qualifying samples.
- **Uncertainty:** These are retrospective, nonmatched/censored traces and do not estimate false interrupts, planner usage/savings, safety, useful action, recovery efficacy, matched tempo, or MAP01 completion. This construction did not replay or rerun the live allocation; it tests the frozen rule's code boundary only. No new model/game/live allocation ran. Keep candidate pending a prospective comparison with an explicitly assigned lane and fixed trigger, false-interrupt, admission, cost, and no-input gates.

## Reproduction

From the repository root, with research Python dependencies available:

    python -m py_compile research/doom/map01_overlap_controller_v40.py research/doom/unauthored_coast_liveness_v1.py
    python -m unittest research.doom.test_unauthored_coast_liveness_v1 -v
    python -m unittest research.doom.test_map01_overlap_controller_v40 -v

Observed construction result: compile exit 0; 9/9 monitor/handoff tests and 3/3 controller integration tests pass.
