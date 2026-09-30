# Arena v1 recovery-boundary construction probe

H: after the forced RECOVERY relocation, reusing the pre-interruption coordinates should fail while reacquiring the current target coordinates should pass the Arena effect scorer.

This is a small deterministic state-machine construction experiment for Issue #4695, not a model or GUI evaluation. Five fixed seeds at difficulty 0.35 used identical generated recovery stages across three cases: stale coordinates, fresh coordinates after querying the current state, and the existing oracle positive control. The original Arena engine/test sources were fetched from main; blob IDs are in RESULT.json. No source behavior or thresholds were modified.

Run from a checkout of main containing `research/procedural_control_arena_v1`:

```sh
docker build --network=none -t arena-recovery:local -f research/procedural_control_arena_v1/Dockerfile research/procedural_control_arena_v1
docker run --rm --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --memory=1g --cpus=1 --pids-limit=64 -v "$PWD/research/experiments/procedural_arena_v1_recovery_boundary_4695_v1:/probe:ro" -w /src arena-recovery:local python -m unittest -v test_engine
docker run --rm --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --memory=1g --cpus=1 --pids-limit=64 -e PYTHONPATH=/probe:/src -v "$PWD/research/experiments/procedural_arena_v1_recovery_boundary_4695_v1:/probe:ro" -w /src arena-recovery:local python /probe/audit_probe.py
```

Observed: existing unit tests 14/14 PASS; stale reuse failed 5/5; fresh reacquisition passed 5/5; oracle controls passed 5/5; independent compact auditor had zero errors. The probe is deliberately CPU-only; a GPU has no role in this deterministic state transition.

The preregistration was not made before the probe; this is reported as a posthoc construction diagnostic, not formal evidence. It does not demonstrate that an agent can perceive relocation or reacquire under realtime GUI/model latency. Only the compact rows needed to verify these gates are published to keep the evidence handoff small.
