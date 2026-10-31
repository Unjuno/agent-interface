# Exploratory WSLc Freedoom MAP01 threat route

These are seven separate exploratory allocations using the pinned Calc/ViZDoom image and current-main guarded X11 bridge, private Xvfb, one CPU, no container network, Freedoom2 MAP01, skill 1 and seed 991031. No model or adaptive policy was invoked. Each was a new attempt; conditions and earlier failures remain unchanged. The controller uses fixed timed keys and screenshots; game state, visible labels and object inventory are recorded for evaluation only and not used to choose an action inside a run.

| Run | Observation |
| --- | --- |
| e01 | no-input control: health remained 100, no visible enemy label |
| e02 | forward/use/forward: health 100, no visible enemy label |
| e03 | same route with object inventory: initial world state contained 10 `Zombieman` and 1 `DoomImp`; no visible enemy label |
| e04 | after moving to a wall, the old anchor became flat; mint refused before turn; earlier inputs released |
| e05 | reviewed a different textured anchor in a fresh run; turn input completed but game angle remained 0 degrees |
| e06 | enabled `TURN_RIGHT`; same turn changed game angle from 0 to 309 degrees; wall still limited travel |
| e07 | alternate left-turn route: `Zombieman` appeared in visible game labels at tic 172; health first observed below 100 at tic 287 and ended at 84 |

In e07 all three recorded input operations completed and verified empty releases; final key readback and owner-close release were neutral. The visible label and later health decrease establish that the environment exposed an enemy and damage in this bounded episode, but do not prove which actor caused the damage. The exact time of impact lies between sampled game tics. There was no kill, model inference, model-selected action, threat-policy handoff, comparison of cover strategies, recovery demonstration, or MAP01 exit. e07's route was selected after inspecting earlier diagnostics, not frozen before the whole search; it is a development discovery, not a held-out benchmark or reliability estimate. e04's runner catches exceptions, so its zero container exit is not a successful run.

Each archive retains the script, conditions, telemetry samples, screenshots, owner evidence and logs. `python audit.py` checks all seven, validates input and game-state ordering, release records, object counts, angle changes and the visible-enemy/damage observations. Raw engine object data is privileged evaluation telemetry; an image-only agent would not receive it. The next experiment can freeze this newly discovered route and compare live control during an actual model call against suitable controls, while preserving this discovery separately.
