# Shared bounded two-phase caller

phased_submit_v1.execute(call, proposal, checked, source) extracts the measured
activation/handoff/keyboard sequence into a reusable caller. `call` must wrap
durable_submit_v4.run and return its validated result; `checked` is a previously
evaluated sampled target contract. The helper validates the numeric proposal
subset before transport, permits one initial click and a keyboard-only tail,
and copies the proposal so its caller cannot change it midway through execution.

Activation retains the target-contract deadline. A completed activation is
followed by clock/observe/clock. Only a completed, released observation program
and a passing post-activation handoff allow a separate two-second keyboard
program. Checking observation-program completion is stricter than the original
experiment's pending-only observation check. Program completion requires a
matching ID, every step completed, no interruption and verified empty release.

Normal refusal returns a structured reason and the received exchanges.
Transport exceptions propagate; the durable journal preserves uncertain
delivery for explicit reconciliation. No loop retries activation or the tail.
The result's completed status is program completion, not saved-task scoring.
This remains opt-in, restricted to the existing numeric keyboard proposal
subset, and requires a single coordinated durable caller. It does not make
same-window widget targeting atomic or establish semantic focus.

Eleven controls replay the archived phased-replan transport and modify selected
responses to exercise pending activation, expired activation, unresolved clocks,
expired observation, changed focus, moved pointer, expired tail and lost replies.
They verify exact outgoing commands and exchange counts: no tail is sent when
the handoff fails, and no tail is resent after uncertain or interrupted delivery.
Evidence is results/phased-submit-controls-01. These are synthetic faults on
recorded responses, not live inter-phase fault injection.

shared_phased_ink_v1.py integrates the helper into the actual model-driven
reselection/edit/verification episode. Its separate audit retains full event,
frame, journal, model provenance, deadline, handoff and artifact checks.

The fresh shared-helper episode completed all programs and independently saved
X104/Y50/W40/H30. Audit passed for173 events,27 exact frames,55 journal records
and27 durable exchanges. Four model calls used44,860 input tokens (22,528
cached) and720 output tokens. Handoff took323.999ms. This confirms live
integration of the extracted helper, not a speedup or cross-domain validation.
Next exercise the boundary under a real state change, then apply the shared
caller to a different desktop interaction rather than repeat this coordinate
case. Evidence: results/shared-phased-ink-01.
