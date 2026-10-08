# OpenTTD explicit point-contract transfer, v1

## Decision

**HOLD_AND_PRESERVE.** The explicit point-space and motion contract transfers to
OpenTTD, but direct semantic point grounding fails in both preregistered cases.
The runtime correctly preserves and moves the regions the model selected; those
regions are the wrong toolbar icons. This is a useful cross-domain failure and
must not be repaired by retrying the same allocation.

## Preregistered test

Two fresh Linux/X11 OpenTTD 13.4 sessions use the same seed991004 save, task,
1024x720 screen, prompt and Luna-low configuration. The transient-target case
runs first. Each case permits one image call. The model must author:

- a point in `source_observation_pixels`;
- either `surface_origin_translation` or `screen_fixed` motion;
- the Road Construction toolbar opener as the semantic target.

The runtime derives a fixed24x14 patch from that point. Stable then requests a
surface move and uses the window manager's observed delta for the handle, road
path and local condition. The paired negative clicks the independently known
Road Construction opener after model return; the selected patch was expected to
change and refuse minting. The five-tile L has a separate engine scorer. The
failure policy forbids retries or prompt, point, frame, size and order repairs.

## Result

Both calls correctly return `source_observation_pixels` and
`surface_origin_translation`. Neither grounds the intended icon:

| Case | Model point | Known target | Reported input | Outcome |
| --- | ---: | ---: | ---: | --- |
| transient target | `[650,51]` | `[820,51]` | 9,297 | wrong patch remains unchanged, so mint succeeds instead of refusing |
| stable | `[432,51]` | `[820,51]` | 9,296 | wrong-icon handle follows the surface move; task stops locally |

The known target is independently retained from the earlier successful scripted
OpenTTD run as point `[820,51]` inside box `[812,43,16,16]`. The two new model
points differ from that target and from each other despite identical task text
and save. The top toolbar is a dense row of unlabeled icons, so a single full
frame does not provide a reliable semantic label for this target.

In the transient case, the known click at `[820,51]` receives the expected move
and button-down admissions. Because the model chose `[650,51]`, its derived box
`[638,44,24,14]` does not change. Source and fresh patch digests match, and the
runtime correctly mints a handle for that unrelated icon. Independent task
success is false.

In stable, the derived box is `[420,44,24,14]`. The requested surface move
`[20,8]` is realized by the window manager as `[21,28]`; handle check and input
admission both revalidate the selected region at point `[453,79]`. The first-road
condition measures12 target pixels and0 guard pixels against a120-pixel target
minimum, stops at step4 as `needs_decision`, and verifies release. No later road
mutation is admitted. The independent target and connection checks are false;
forbidden and surrounding checks remain true.

Stable takes18.629s from decision start to independent evaluation, including
14.209s in the parent-observed model call. Transient takes17.659s, including
14.898s in the model call. These are single failed episodes and support no
speed comparison.

## Audit and interpretation

The audit independently checks all frozen source hashes, identical prompt and
model configuration, the prior successful target, point/box geometry, source and
fresh patch digests, surface translation, admissions, local stop, engine score,
cleanup and verified releases. It reconstructs28 transient and34 stable frames
from the binary stream and matches the PNGs on Windows and WSL. Both saves remain
unchanged and all owned processes exit. The OpenTTD X server teardown may print
an XIO line after shutdown; bridge exit0 and cleanup ownership are the lifecycle
criteria used here.

This result separates two capabilities that the Chromium result had conflated:

1. The interface can carry an explicitly authored source pixel and motion model,
   mint its visual region and track a real surface translation.
2. A planner can still bind that valid contract to the wrong semantic object.

The local condition contains the second failure before the remaining task
mutation. That is a safety result, not task correctness.

## Next experiment

Test bounded hover-label evidence for a preregistered toolbar candidate set.
OpenTTD already has delayed-tooltip contact-sheet machinery, so the next study
should reuse it instead of adding unbounded screenshots. The model should select
among fixed candidate points after seeing their delayed tooltips; the runtime
then uses the same explicit point/motion contract and independent engine score.
Preregister tooltip readiness, readable evidence and candidate-to-tooltip
association rather than assuming that the contact sheet proves them. Include a
wrong-label or changed-tooltip negative and compare model boundaries, input
tokens, target accuracy, semantic completion and recovery cost. Direct full-frame
point selection remains the preserved baseline.

Sources and raw evidence:

- `preregister_openttd_point_contract_pair_v1.py`
- `run_openttd_point_contract_pair_v1.py`
- `audit_openttd_point_contract_pair_v1.py`
- `results/openttd-point-contract-pair-01/`

Scope is two fresh same-save cases and one known toolbar target. Region size is
still caller-authored. The study establishes no unseen-task grounding, cost,
causal speed, broad token reduction or human-tempo performance.
