# Combined fresh observation and target-handle check

Status: cross-domain scripted replication passed; opt-in candidate.

`session_v32.py` adds one bounded read-only operation:

```json
{"op":"observe_target_handle","target_handle":"save_form","offset":[20,9]}
```

The operation captures an exact fresh frame first and then resolves the private-ID-backed
session alias against that same observation. Its response contains both `observation` and
`target_handle_checked`; the latter records the exact observation sequence and capture time.
It grants no input authority. A later `pointer_click_target` still performs the existing
admission-time handle resolution and ordinary focus, surface, geometry and input-owner checks.

## Fresh matched integration

The preregistered `chromium-observe-target-pair-01` allocation uses two new isolated X11
sessions with seed991012. Both navigate to the same form, type the same value, mint the same
Save alias, observe the same `[20,8]` client translation and click the same `[20,9]` relation.
The only fixed difference is the read-only pre-action path.

| Arm | Read-only workflow | Durable calls | Exact frames | Independent save |
| --- | --- | ---: | ---: | ---: |
| combined | one `observe_target_handle` submit | 12 | 14 | 1/1 |
| separate | `observe`, then `target_handle_query` | 14 | 15 | 1/1 |

The combined check's sequence and capture timestamp equal the observation returned in the
same response. Both admission revalidations are `REVALIDATED`, both clicks have exactly two
pointer admissions, both terminals verify release, and the independent oracle receives exact
`t991012`. All29 frames replay exactly on Windows and WSL.

The observed workflow return was202.583ms combined and365.441ms separate. There is one case
per arm, so this is descriptive and does not establish a causal latency distribution. There
are no model calls or token measurements in this allocation. The prior model-facing ABBA
already showed why the extra query mattered: its handle arm used16 durable calls versus14
for coordinates. Integrating this operation at that boundary is the next model test after a
different-domain replication.

The initial probe attempt failed on Windows before execution because it imported X11 code;
two extracted-probe wiring mistakes then failed identically on Windows/WSL. These failures are
listed in the preregistration. The final X11-independent operation probe and alias regression
both pass on Windows and WSL.

## Evidence

- Preregistration and artifacts: `results/chromium-observe-target-pair-01`
- Audit: `python research/live_control/audit_chromium_observe_target_pair_v1.py`
- Pure controls: `python research/live_control/probe_observe_target_handle_v1.py`

## OpenTTD cross-domain replication

A preregistered fresh seed991004 episode uses the same combined operation for the Road
Construction toolbar, then executes the existing two-drag L task. The combined result is
bound to observation sequence17/capture time, resolves `[820,51]`, and is resolved again at
input admission. The first-segment local condition sees160 changed target pixels and zero
guard pixels, so the continuation runs. The independent game oracle then passes owned target
roads, all ordered bidirectional connections, the forbidden row and unchanged surrounding
guard tiles. The terminal releases all input, the immutable save remains unchanged, all
processes exit, and37 exact frames replay on Windows and WSL.

The combined observe/check returns in234.989ms and the complete eight-step local program in
3956.186ms. These are one scripted episode with development-known geometry, no model call and
no matched separate-query arm. They do not establish a speed or generalization effect.

- OpenTTD artifacts: `results/openttd-observe-target-live-01`
- OpenTTD audit: `python research/live_control/audit_openttd_observe_target_live_v1.py`

This supports retaining the combined operation across two control domains. It does not
promote target handles as a default interface or support a token, general speed or human-tempo
claim. The next strong test should integrate it at a model boundary on a new task and include
a changed-target refusal or matched negative allocation.

## Model-boundary and stale-target pair

A second preregistered pair uses two fresh seed991013 Chromium sessions with the same exact
prompt, no image, Luna-low and controlled empty workspace. Both model calls return the strict
`save_form` relation and report8,013 input tokens with zero within-pair variance.

The stable arm takes a post-model fresh observation, revalidates `save_form`, admits exactly
move/button-down, saves exact `t991013`, verifies release and passes independent evaluation.
It uses14 durable calls, versus16 in each prior separate-query model-handle case.

In the changed-target arm, the same Chromium surface navigates to `about:blank` after the
model returns. The required post-model observation sees the new page. Admission-time handle
resolution returns `MISSING/region_pixels_missing`; the proposed target click receives zero
pointer admissions, the terminal is `needs_decision`, release verifies and no submission file
exists. Independent evaluation remains false. Across both arms,37 exact frames replay on
Windows and WSL.

The stable decision-to-independent-return interval is5,998.963ms; changed-target is
11,435.887ms and includes the deliberate navigation plus failed independent lookup. They are
not a matched latency comparison. Cost remains unavailable, and the 8,013-token result repeats
one controlled prompt rather than proving broad compression.

- Model-pair artifacts: `results/chromium-observe-target-model-pair-01`
- Model-pair audit: `python research/live_control/audit_chromium_observe_target_model_pair_v1.py`

This closes the immediate model-boundary and stale-target gates. The next useful comparison
should change the task/domain or derive target identity with less human-authored geometry.
