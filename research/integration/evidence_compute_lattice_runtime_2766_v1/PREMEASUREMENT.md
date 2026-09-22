# #2766 premeasurement freeze — corrected before formal

Intake main: `3f79994b4dda589951e2ddfe062215bb4a944d70`. Branch: `research/evidence-compute-lattice-runtime-2766-20260922`. Additive namespace: `research/integration/evidence_compute_lattice_runtime_2766_v1/**`.

Formal rows: **0/18**. Formal reruns/replacements: **0/0**. Construction is excluded. The first unit invocation stopped on module search path before scientific cases; corrected invocation passed. Four construction probes exercised cached mismatch, measured RUN, compute invalidation, and measured rebuild. None is pooled.

A first public premeasurement snapshot was read back exactly, then static review found that `cached_reuse_at_deadline` was not actually pinned to `t == deadline`; it had the normal 50 ms margin. Before any formal row, `run_case.py` was corrected only to set that case's deadline exactly to the decision sample and one regression unit was added. No scientific policy, threshold, arm, or post-result information changed. The earlier public snapshot remains in Git history as a preformal provenance incident.

H/T/D/C/U and the frozen decision gates are in `PLAN.md` inside the source archive. The scientific policy is the unchanged #1702 order: cached version→deadline; active version→t+remaining deadline→expected RUN/WAIT/TIE. REBUILD_REQUIRED never implicitly executes.

Exact corrected source archive: 7240 bytes XZ, SHA-256 `b0f9f1a7e8e13f7f282c764cfe2cb442a7bac18de7aadb1672e6de3aba7369b8`, 9 members. `FREEZE.json` binds every member SHA-256 and the fixed 18-case/two-batch schedule. Six unit methods pass.

Formal commands after corrected GitHub readback only:
```
python -B run_formal.py --out formal/batch-0 --batch 0
python -B run_formal.py --out formal/batch-1 --batch 1
python -B audit.py formal --out AUDIT.json
python -B controls.py formal > CONTROLS.json
```

No model/provider, GUI/input, experiment network or Docker/OrbStack replication claim. #2806 remains the separate deployment-probability calibration question.
