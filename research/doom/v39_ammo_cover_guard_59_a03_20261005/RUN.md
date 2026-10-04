# A03 run record

- Base: `e561b25b700680df4e6ffd2b92faf1dde1682ef7` (`origin/main` at freeze).
- Runtime: Windows host, CPython 3.11.9, stdlib only; no container or isolation claim.
- A preliminary invocation without `PYTHONPATH=research/live_control` stopped at import resolution before running any case; no output was written. Corrected the command before the one successful probe invocation. The independent auditor ran once after the result existed.
- Probe: `PYTHONPATH=research/live_control python -B research/doom/v39_ammo_cover_guard_59_a03_20261005/probe.py`
- Audit: `python -B research/doom/v39_ammo_cover_guard_59_a03_20261005/audit.py`; the first independent audit scored 25/26 because its status oracle mislabeled a coherent but guard-invalidated frame. That raw audit is preserved as `AUDIT_INITIAL.json`. After correcting only the oracle label and without rerunning the probe, the second audit passed 26/26 as `AUDIT.json`.
- Formal/live allocations: 0. Game/model/GUI/OS input: not invoked.
