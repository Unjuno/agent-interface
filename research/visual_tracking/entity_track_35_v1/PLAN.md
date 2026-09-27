# Prospective plan — bounded EntityTrack continuity for Issue #35

Allocation: entity-track-live-20260922-01

H: A short-lived visual EntityTrack that is initialized from an actually marked target, then updated by exact current red-component geometry and bounded constant-velocity association, can complete separable-motion cases with fewer NEEDS_DECISION outcomes than a current-frame candidate-set policy while making zero wrong-entity actions. Ambiguous crossing, disappearance/reappearance, replacement-after-loss, and stale-current evidence must YIELD before input.

T: private Xvfb/Tk Canvas. Three policies: SINGLE_FRAME_FIRST, CANDIDATE_SET, ENTITY_TRACK. Eight fixed scenarios x two repetitions = 48 fresh app cases. The task is always "move the rectangle that was blue-marked in observation 0". The marker is removed after observation 0. All policies get the same exact current pixels; ENTITY_TRACK additionally retains bounded observation-0/1 geometry history. A fresh capture immediately before XTEST click is mandatory. The app moves whichever rectangle actually receives the click; an independent raw scorer compares object coordinates before/after. No model/provider/network/user desktop.

Scenarios: SINGLE_TARGET, FAR_DISTRACTOR, ORDER_SWAP, CROSSING_AMBIGUOUS, OCCLUDE_REAPPEAR, DECORATION_CHANGE, REPLACEMENT_AFTER_LOSS, STALE_AFTER_CAPTURE.

D: PASS_ENTITY_TRACK_CONTINUITY_SCOPED only if all 48 cases and process/source/effect/cleanup evidence reconcile; ENTITY_TRACK has zero wrong actions, succeeds in both repetitions of SINGLE_TARGET/FAR_DISTRACTOR/ORDER_SWAP/DECORATION_CHANGE, and yields in both repetitions of CROSSING_AMBIGUOUS/OCCLUDE_REAPPEAR/REPLACEMENT_AFTER_LOSS/STALE_AFTER_CAPTURE; CANDIDATE_SET has zero wrong actions but fewer successful task effects than ENTITY_TRACK; SINGLE_FRAME_FIRST exposes at least four wrong-entity actions; every terminal key/button state is neutral; independent raw-only audit has zero errors and rejects >=8 copied-evidence corruptions.

C: Exact red-color Tk fixture, two objects maximum, cooperative app state journal, deterministic barrier-selected trajectories. This does not solve semantic identity when observations are pixel-identical; after LOST, reappearance remains ambiguous by construction. The association algorithm is deliberately small and finite, not a general tracker.

U: Inkscape transfer, arbitrary decoration/scale, >2 objects, partial occlusion, compositor/Wayland, learned perception, model utility/tokens, natural failure probability, performance benefit, and production action admission remain unknown. Entity IDs remain authority-neutral and fresh click admission stays separate.

Roadmap: collision/source check -> publish plan/source freeze -> excluded construction -> single formal 48-case allocation -> independent raw audit/corruption controls -> additive PR -> inspect exact-head CI/review -> merge only if qualified -> main readback -> clean only owned dependency-safe branch if a supported deletion action exists.
