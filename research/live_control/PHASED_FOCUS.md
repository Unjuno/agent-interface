# Real inter-phase focus fault

probe_phased_focus_v1.py exercises the unchanged phased_submit_v1 caller against
a fresh private Xvfb/Inkscape instance. Selection, activation and the intended
X104 edit are scripted; there are zero model calls. A sampled pixel contract
admits the X-field click. Immediately after that activation completes with
verified release, the harness creates an override-redirect sink on this bridge's
own descendant Xvfb and moves the actual X input focus to it.

The caller still performs its bounded clock/observe/clock handoff. The new
capture records the sink's focus before and after capture, and the unchanged
handoff gate refuses with binding_changed_or_missing. No keyboard tail, text,
Ctrl+A or Save is submitted. Focus restoration and sink destruction occur only
as cleanup; the old proposal is not replayed. Saved geometry remains
X50/Y50/W40/H30. This is successful refusal, not successful editing.

The measured handoff took276.038ms. Four phase exchanges occurred: activation,
clock, observation, clock. Full audit covers58 events,8 exact frame/PNG pairs,
12 durable exchanges, journal/continuation replay, recorded pixel and handoff
checks, actual sink focus in the post-terminal observation, completed released
programs, two pointer clicks total, no keyboard commands, unchanged SVG and
normal process/socket cleanup. Results are in results/phased-focus-01; use
audit_phased_focus_v1.py for read-only replay under Linux.

Limits: this fault happens before the new handoff sample and demonstrates that
detectable X focus changes prevent continuation. It does not cover a change
after the final check, same-window widget focus changes, OS scheduling races,
or recovery planning by a model. The helper still uses sampled context and
explicit deadlines; it makes no atomic semantic-target guarantee. No new
runtime/caller revision was needed for this test.

Decision: retain the shared caller as an opt-in candidate with both successful
live operation and real inter-phase refusal evidence. Next apply it to a
different desktop task and evaluate observation/round-trip overhead there.
Do not continue this single-coordinate Inkscape chain as a substitute for
domain coverage or human-like live-tempo evidence.
