# A01 run record

- Commit/source base: `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Runtime: CPython 3.14.5, macOS arm64; stdlib-only monitor boundary, no isolation claim.
- Docker: OrbStack Engine 29.4.0 answered, but `docker image ls` failed read-only because a cached containerd blob could not be opened (`operation not supported`). No pull/build/restart/repair.
- Exact execution: `PYTHONPATH=research/live_control python3 -B research/doom/v39_ammo_cover_guard_59_a01_20261005/probe.py` → exit 0, wrote `RESULT.json`; then `python3 -B research/doom/v39_ammo_cover_guard_59_a01_20261005/audit.py` → exit 0, 7/7 checks.
- Formal live allocation: 0. Probe invocations: 1. Auditor invocations: 1. Retries: 0.
- Outcome: `FAIL_AMMO_DEPLETION_NOT_GUARDED`; zero-ammo did not invalidate the health-bound cover monitor; unchanged positive ammo was preserved; health below hard minimum invalidated.
- No game, model, GUI, OS input, physical release, actual cover renewal, task effect, or live threat exposure occurred.
