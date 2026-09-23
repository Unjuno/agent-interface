# Input response and rendering diagnostics

Four exploratory single-case cohorts use seed 990301 and the pinned shared
input backend. Each holds a key for one second, waits one second, then observes.
The diagnostic adapter reads initial angle before control and final state only
after executor closure; it also saves an X11 image after the final engine refresh.
No controller action is chosen from engine telemetry. Source/case manifests and
failed hypotheses are retained. These are not counterbalanced efficacy studies.

| Cohort | Change | Observed result |
|---|---|---|
| response-01 | Right hold; normal refresh schedule | Angle 0 -> 0; unfinished; 10 exact frames |
| refresh-diagnostic-01 | Refresh engine state before every screenshot | Angle 0 -> 0; unfinished; 9 exact frames |
| attack-response-01 | Space hold; normal refresh schedule | Ammo 50 -> 49; finished and alive; 12 exact frames |
| delta-response-01 | Add TURN_LEFT_RIGHT_DELTA to allowed buttons, Right hold | Angle 0 -> 0; position unchanged; unfinished; 12 exact frames |

The attack trial's saved image shows the finish screen. This establishes actual
game response through the shared input owner in this one scripted case. It is
not assistant gameplay or broad skill. The score reports episode_tic=0 on the
finished episode; do not interpret that as zero elapsed gameplay time. The
initial/after-control telemetry records are diagnostic artifacts, not observations
fed to the controller. Post-control snapshots must be excluded from feedback
latency metrics.

The initial two-second clock probes are near 35 tic/s. They precede control and
do not validate the clock throughout the refresh-per-observation candidate.
That candidate also changes reward update frequency (-12 versus -3), so its
reward must not be treated as a directly comparable task-quality measurement.
Neither refresh-per-image nor adding the delta button resolved the turn symptom;
neither is promoted into the shared runtime or default DOOM entrypoint.

An early hypothesis was a basic-scenario restriction. The installed basic.cfg
lists lateral movement and attack, but the adapter explicitly replaces that list.
Inspection of the installed WAD's SCRIPTS lump shows target placement, target
immobility/one-hit health and reward handling; it does not establish a player-turn
restriction. Consequently a scenario lock is **unproven**. Likewise no input-wide
failure can be claimed given the successful shot. The earlier black image was
not reproduced in these short probes and remains unresolved.

The installed API documentation says get_game_variable can query variables not
listed in the state, but can return zero when unavailable. The unchanged angle
therefore needs a positive control rather than being sufficient by itself to
prove absence of rotation. The next useful check is a reference keyboard path
and observed key binding/engine response, followed by fresh shared self-use once
directional input is verified. Do not mask the issue by choosing only centered
targets or declaring shot-only correctness to be the final goal.

Run `python research/doom/audit_response.py` to verify all four source manifests,
43 exact frames, terminal releases, owner closure, full delivery and the recorded
post-control outcomes. All cohorts retain their narrow readiness flags; these do
not mean full task correctness. Research Freeze remains unqualified.

References: [DoomGame API](https://vizdoom.farama.org/main/api/python/doom_game/)
and [button/mode definitions](https://vizdoom.farama.org/api/cpp/enums/).

## Follow-up resolution of directional input

[BINDINGS_FIX.md](BINDINGS_FIX.md) records the arrow-name correction and fresh
directional response, followed by successful actual assistant gameplay in v7.
The historical failure/diagnostic evidence above remains unchanged.
