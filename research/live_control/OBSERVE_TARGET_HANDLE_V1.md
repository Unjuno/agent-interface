# Combined fresh observation and target-handle check

Status: advance to cross-domain replication; opt-in candidate.

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

This advances the combined operation to a task with different control semantics and an
independent semantic endpoint. It does not promote target handles as a default interface or
support a token, general speed, human-tempo or cross-domain claim.
