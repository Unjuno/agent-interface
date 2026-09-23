# Directional bindings fixed; shared assistant gameplay succeeds

The frozen adapters used `left`, `right`, `up`, `down` in Doom.Bindings. These
are not the working arrow-key configuration names in the installed engine.
`session_v7.py` changes them to `leftarrow`, `rightarrow`, `uparrow`, `downarrow`.
The action strings (+left/+right/+forward/+back) are unchanged. Relative to v6,
the only other change is the source manifest's own filename. There is no common
backend, deadline, ownership, focus or executor semantic change.

## Evidence for the correction

The installed executable contains the four arrow names. More importantly, the
same-seed diagnostic comparison isolates the binding change: response-01 had a
one-second Right hold with angle 0 -> 0; bindings-01, otherwise the same diagnostic
setup and seed 990301, changed angle 0 -> 242.227 degrees. The world view changed
before post-control engine refresh. This is directional correctness evidence,
not a speed comparison. Frame timing differs between independent launches.

Fresh cases use 250 ms holds and seeds 990401–990404:

| Key | Post-control result | Exact frames |
|---|---|---:|
| Left | Angle 0 -> 26.367 degrees | 6 |
| Right | Angle 0 -> 323.086 degrees | 6 |
| Up | X -384 -> -284.607 | 7 |
| Down | X -384 -> -431.915 | 6 |

All four have visible world changes before scoring and verified release/owner
closure. The diagnostic development case adds 11 frames: 36 total. These narrow
directional cases do not complete a game and do not qualify Research Freeze.
Run `python research/doom/audit_bindings.py` to verify sources, frame transport,
delivery, cleanup and state changes. The crop comparison is an offline response
check, not a general scene-understanding oracle.

The previous scenario-lock hypothesis is superseded for these directional keys.
The extra-refresh and delta-button experiments remain negative evidence; neither
is part of v7. Earlier readiness flags only proved input admission/cleanup. Their
claims must not be read as game-response correctness. The separate black-screen
incident's root cause is still unproven; correcting bindings is not proof that
black output can never recur.

## Actual assistant self-use

`shared-assistant-02`, seed 990501, runs the normal `session_v7.py`, without the
diagnostic state reads or extra post-control snapshot. The assistant inspected
001.png, saw the target left of center, and issued a 100 ms Left hold. After
inspecting 003.png it made a 60 ms Left adjustment followed by a 350 ms Space
hold. It inspected 007.png showing FINISHED, then ended control. Only afterward
the engine score reported episode_finished=true and player_dead=false, reward 98.
This is a successful basic-room assistant task with two accepted programs, not
full-game competence. No hidden engine state selected controller actions.

All nine frames reconstruct exactly, both programs verify release, raw/delivered
records match, and owner shutdown is verified. The initial clock probe observed
34.967 tic/s. The final episode_tic=0 is an engine terminal-state value, not zero
elapsed time. The initial capture to first acceptance took 20.468 seconds and
the two acceptances were 20.974 seconds apart. These runtime-clock intervals
include tools, image inspection and reasoning. Actual model tokens and receipt
latencies are unavailable; there is no human-tempo or token-savings claim.

Use v7 for the next common-runtime self-use. Remaining priorities include reducing
the observed planner/tool gap with comparable measurements, continued long-gap
render checks, shared stress coverage and continuous tracking transfer. The goal
remains active; this is a concrete adapter correctness fix, not architecture freeze.
