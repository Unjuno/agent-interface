# Issue #6617 T0 result: PASS_METHOD_SCOPED

The frozen candidate and independent auditor each ran once and exited 0.
All 30 policy/scenario rows were independently reconstructed with no errors.
On the single stable scripted request, final-only verified at 220 ms and
version-bound read-only preparation at 150 ms, a 70 ms simulator reduction.

Across all 10 scenarios, version-bound outcome and issued-action sequences
matched final-only exactly: zero stale/provisional/duplicate actions, zero
outcome mismatches, and physical release preserved. The naive provisional
policy emitted a consequential event on seven scenarios. The auditor rejected
all four corruptions: old epoch reuse, accepting a partial as final, merging
speakers, and treating STOP as undo.

## Limits

This is only a scripted finite event contract. The time units are authored
simulator quantities, not measured ASR latency or interaction speed. There was
no audio, microphone, ASR/model, participant, GUI, live input, or real effect.
It does not establish spoken-intent accuracy, usefulness, real-time safety,
or product voice UX. The stable-turn time gain is a conditional synthetic
result; the one stable case is not a distributional estimate.
