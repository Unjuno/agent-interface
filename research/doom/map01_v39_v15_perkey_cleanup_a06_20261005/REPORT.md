# A06 result — STOP before the release test

The frozen candidate ran once against current main `10be950b8fb6e2799b837b541577fb5f32db858d` in the pinned WSLc Python image. Both normal and injected-loss arms were submitted, but ExecutorV13 rejected the harness step before the action loop: the fixture supplied `actions` without the required `op` field. Both terminal rows report `failed`, `KeyError('op')`, and `steps_completed: 0`. No release-transition row was emitted and the dropped-KeyRelease injection was never reached.

The candidate itself exited 0 after retaining both rows. The frozen independent auditor returned `FAIL_RAW_OR_SOURCE_AUDIT`, 18/30. Its failed checks are the preregistered terminal/release/attempt expectations for both arms; its source snapshot, manifest, schema and provenance checks passed. The fake server's empty keymap is its initial neutral state, so it does not show successful release recovery. Disposition: `STOP_BEFORE_TREATMENT_ACTION_SCHEMA_MISMATCH`. Candidate was not rerun.

The exact stdout/stderr summaries, candidate raw and auditor output are preserved in `RUN.json` and `results/`. The system warned that swap limits are unsupported; `memory.max` was 536870912 and `memory.swap.max` was `max`.

This attempt establishes only that the frozen synthetic harness used the wrong ExecutorV13 step schema. It says nothing about production KeyRelease retry behavior, X11 delivery, physical keys, application effects, useful feedback, threat response, recovery efficacy or MAP01. No live or formal #59 allocation was used.

See `PLAN.md`, `FREEZE.json`, `PREFLIGHT.json`, the 21-file source manifest/snapshots, raw candidate result, and the frozen independent audit.
