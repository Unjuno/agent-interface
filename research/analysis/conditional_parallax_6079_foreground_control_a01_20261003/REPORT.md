# #6079 foreground-dominance control A01

**Disposition: `CONTROL_EXPOSED` — generic feature transfer is unsafe without independently grounded layer identity.** The frozen #6079 candidate returned `DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS` on a noncontact sham control even though target-intensity pixels were unchanged across the paired observations. The only changed content was a synthetic 40×12 foreground patch rendered at the candidate's accepted landmark intensity in one member's three post-probe frames. The independent auditor found 0 px target separation but 50.712652 px candidate-statistic separation in each post-probe frame.

This is a falsifying counterexample to using the frozen all-landmark centroid as a generic scene-parallax statistic when non-rigid foreground layers can be included in the landmark set. It does **not** contradict parent allocation `CONDITIONAL-PARALLAX-6079-T0-20261003-01`: that result is explicitly conditioned on a rigid landmark field and remains preserved unchanged. No candidate contact claim or authority was produced. This control does not establish behavior on any real sensor, GUI, or game.

## Method and provenance

- Parent sham `pair-04` was copied from the frozen visible corpus; parent source and corpus hashes are recorded in `FREEZE.json`.
- Passive frames and all target-intensity pixel positions were checked unchanged. A synthetic nonzero probe receipt exercises the same frozen decision path; no physical probe occurred.
- Construction test: 1/1 passed before formal freeze; source syntax check passed.
- Frozen candidate invoked once, exit 0; independent raw-only auditor invoked once, exit 0; no retries. Raw one-pair input/output, stdout/stderr, and audit output are retained here.
- Runtime was CPython 3.14.5 on Darwin 25.6.0 arm64, host CPU and standard library only. No container/model/network/GUI/game/OS input/GPU/shared runtime.

## Integration consequence

Any future extension beyond the authored rigid-background fixture must bind the target and background layers to independent identity/geometry evidence, and include dominant-foreground controls. If that information is absent or ambiguous, return `UNKNOWN`. Re-estimate a threshold or globally widen/narrow the search is not supported by this control. No code fix or feature promotion is made in this diagnostic allocation.
