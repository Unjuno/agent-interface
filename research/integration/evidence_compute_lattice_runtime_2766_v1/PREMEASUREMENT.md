# #2766 premeasurement freeze

Intake main: `3f79994b4dda589951e2ddfe062215bb4a944d70`. Branch: `research/evidence-compute-lattice-runtime-2766-20260922`. Additive namespace: `research/integration/evidence_compute_lattice_runtime_2766_v1/**`.

Formal rows: **0/18**. Formal reruns/replacements: **0/0**. Construction is excluded: the first unit invocation stopped on module search path before scientific cases; after execution-path correction five unit methods passed and four construction probes exercised cached mismatch, measured RUN, compute invalidation, and measured rebuild. None is pooled.

H/T/D/C/U and the frozen decision gates are in `PLAN.md` inside the source archive. The scientific policy is the unchanged #1702 order: cached version->deadline; active version->t+remaining deadline->expected RUN/WAIT/TIE. Rebuild never implicitly executes.

Exact source archive: 7156 bytes XZ, SHA-256 `469dba4c8978d3e333acaa2389436d690f24bc320f1244e1b39bcd3f35c26058`, 9 members. `FREEZE.json` binds every member SHA-256 and the fixed 18-case/two-batch schedule.

Formal commands after GitHub readback only:
```
python -B run_formal.py --out formal/batch-0 --batch 0
python -B run_formal.py --out formal/batch-1 --batch 1
python -B audit.py formal --out AUDIT.json
python -B controls.py formal > CONTROLS.json
```

No model/provider, GUI/input, experiment network or Docker/OrbStack replication claim. #2806 remains the separate deployment-probability calibration question.
