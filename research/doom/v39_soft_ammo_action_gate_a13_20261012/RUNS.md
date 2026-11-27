# A13 run record

- Local CPython 3.11.9 final preflight: 1 invocation, 2 tests passed.
- WSLc 3.0.1.0: image `sha256:6d8a582513d4604fbde4a905c9cb3ceed24766fbc9c0118d6c38eb3d0452bdf6`; one test invocation; exit 0; 2 tests passed on Python 3.14.8.
- Requested limits: `--network none --cpus 1 --memory 512m`.
- Runtime warned that swap limit capabilities are unsupported; memory was limited without swap. No separate cgroup probe was run.
- A13 result: source ammo 6, current ammo 4, soft event preserves prior cover; prompt includes current ammo 4 and exact event summary; synthetic short-fire candidate is `REJECTED_ACTION_NOT_CURRENT` (`ammo_minimum_failed`).
- Positive control at ammo 6: `READY_FOR_FRESH_EXECUTOR_ADMISSION`; `executor_admission=null`; `input_authority_admitted=false`.
- Scope: construction-only. Synthetic planner candidate; no model, executor, live game/control, or end-to-end success claim.
