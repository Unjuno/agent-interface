# A17 r1 construction outcome - preserved FAIL

The frozen WSLc image was invoked once. Both tests failed because the fixture passed literal `ammo=6` to `begin_model_turn` while the frozen expectation required prompt ammo 4. The candidate never reached the recovery-vs-control decision gate, so this is a fixture failure, not evidence about the V39 behavior. Raw output, exit code, image digest, and container inventory are retained. It was not overwritten or retried in place.

A separate construction retry with a new source freeze, image, output path, and run identity is recorded in [`v39_pending_ammo_recovery_a17_r2_20261013`](v39_pending_ammo_recovery_a17_r2_20261013/README.md).
