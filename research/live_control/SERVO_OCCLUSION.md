# Occlusion, positive control and false visual goal — 2026-09-13

**Neither unconditional trimmed tracking nor the new raw-first candidate is
qualified.** Session20 stops even on an unoccluded large-object control. Session21
restores that control but reports a local visual goal when an injected replacement
appears at the target while the real document object has not moved.

## Perturbation method and limits

The probe uses a separate X11 connection to create opaque child windows inside the
original Inkscape surface immediately before the first feedback capture. A partial
case covers a 4×36 px strip; hidden covers the source patch; replacement covers the
source and adds a 48×36 px red child window 24 px to its right. All operations occur
on a private Xvfb session. These are environment-side same-surface appearance
perturbations, not native Inkscape object deletion or document duplication. The
controller is not given overlay metadata and still uses ordinary captured pixels.

Overlays are removed after the servo terminal, then a separate GUI save/settle
program runs. XML independently scores the actual document rectangle. This separates
rendered appearance from actual effect without a controller-side privileged API.
Focus/surface identity remains valid: those guards alone cannot detect this fault.
No claim is made about arbitrary real-world occluders or temporal identity robustness.

## Results retained

| Candidate | Normal | Partial | Hidden | Replacement |
|---|---|---|---|---|
| session20, always trimmed | ambiguous, 0 px | ambiguous, 0 px | lost, 0 px | ambiguous, 0 px |
| session21, raw then fallback | goal, 24 px | ambiguous, 0 px | lost, 0 px | **goal, 0 px** |

The session20 normal control is stored separately in servo-occlusion-control-01.
Its failure prevents interpreting the three stops as an unqualified improvement.
Ten-percent trimming makes neighboring offsets too similar on the larger patch.

visual_anchor_v4 first uses raw matching and invokes the trimmed method only on
`lost`, retaining raw ambiguity. patch_servo_v5 and session21 keep source uniqueness
and all original authority bounds. The normal case then succeeds, but replacement
scores a raw match at displacement 24 with error 0.01545 and margin 0.04214. It emits
local_goal_reached and completed without correcting. Saved x remains 50: task fails.
The actual target's y/size/transform remain unchanged throughout all perturbation
cases. Every recorded terminal releases input successfully.

The interface already marks semantic_effect_verified false. That distinction must
remain explicit: a local visual goal is not a causal or independently verified
application effect. This failure is not repaired by renaming the event or widening
the matching threshold. Input/source identifiers are still not visual object identity.

`audit_servo_occlusion.py` verifies 57 exact frames, listed source hashes, release
states, saved attributes, the normal success and false-goal negative. Normal probe
process exits were observed; separate per-child cleanup attestation remains absent.
No matched end-to-end timing, token savings or general control accuracy follows.

## Research decision

Retain session21 as a failing candidate, not a default CLI or runtime promotion.
Keep the original wrong-anchor case and this false-goal case as different negatives:
one causes wrong-direction motion, the other falsely attributes a rendered effect.
Next evaluate an explicit effect-verification/recovery contract and temporal/action
consistency evidence, with clear assumptions about application dynamics. Repeated
identical frames or source uniqueness alone cannot prove that the original object
moved. Test useful positive behavior alongside every stricter stop condition.
