# MAP01: bounded turning calibration with wait control

Three predeclared WSLc allocations ran the same MAP01 seed, guarded setup, cancellation/release and binding review, followed by 100 ms wait, `a` (left), or `d` (right), in that fixed order. Game-internal angle and ViZDoom enemy label geometry were scorer-only: they were never inputs to control. This experiment did not use a model, aim controller or fire. Labels use coordinates relative to the 640x480 game image.

| Allocation | Intervention | Angle change | Enemy center x before → after | Angle change during 0.5 s coast |
| --- | --- | ---: | --- | ---: |
| aj01 | wait | 0° | 336 → 336 | 0° |
| aj02 | left 100 ms | +5.273° | 336 → 365 | 0° |
| aj03 | right 100 ms | −5.273° | 336 → 306 | 0° |

The direction and visible effect were distinguishable in this fixed-seed sample; guarded actions completed, owner release was verified, and tested keys were up at the end. Each arm has only one observation and fixed ordering. No inference about general calibration, aim accuracy, robustness, task completion, or effect of earlier cancellation follows. The samples report no ammo or kill changes. The coast sample is finite and says nothing about later motion.

`public.zip` contains the runner, frozen conditions, screenshots, game samples, label geometry, guarded-input and release records. `python audit.py` checks runner hash, cancellation/review, release, observed angle and label records; it does not independently rederive labels from pixels. Runtime source was mounted read-only from a local snapshot; its Python file hashes were collected **after** execution in `runtime-source-hashes-postrun.json`, not frozen beforehand. The recorded main SHA is the integration reference, not proof that the mounted snapshot exactly matched that revision throughout execution. This provenance limitation prevents treating these runs as a fully pinned formal experiment.

The next discriminating test can use model-proposed screen coordinates, derive bounded left/right action from their offset without using game-internal scorer data, then observe a fresh image and measure whether error is reduced; predeclare no-turn control, stop rules and frozen runtime inputs. This calibration alone does not validate such a controller.
