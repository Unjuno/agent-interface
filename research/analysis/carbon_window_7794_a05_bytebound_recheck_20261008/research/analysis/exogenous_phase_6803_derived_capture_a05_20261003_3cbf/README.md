# Source-derived cue phase, #6969 successor of #6803

Start with [REPORT.md](REPORT.md) and [RUN.json](RUN.json).
Formal result: PASS_METHOD_SCOPED; HOLD_LIVE_TRANSFER. No real-interface claim.

- [PREREGISTRATION.md](PREREGISTRATION.md), [PREREGISTRATION_02.md](PREREGISTRATION_02.md): exact H/T/D/C/U and command-only successor.
- [PREFLIGHT_01.md](PREFLIGHT_01.md), [FREEZE.json](FREEZE.json): initial pre-stage socket STOP, zero formal starts. Original source bytes are in commit 82100b79c845db3200d9637e070f6bde86db8832, not silently rehashed against today's revised runner.
- [FREEZE_02.json](FREEZE_02.json), [STAGING_02.json](STAGING_02.json): unchanged scientific hashes and separate read-only source custody.
- [formal_02/](formal_02/): consumed allocation marker, exact Docker receipts/inspect, observed cgroups, candidate/probe/auditor outputs, mutation copies and all stdout/stderr (including empty logs).
- [MANIFEST_SHA256.json](MANIFEST_SHA256.json): every retained package file except the manifest itself.
- [LOCAL_CI.json](LOCAL_CI.json): all 26 existing Analysis Index Python commands; two provenance assertions failed locally because the separate workflow-restore step was not reproduced.

Safe read-only checks from repository root:

```bash
python -B -m unittest discover -s research/analysis/exogenous_phase_6803_derived_capture_a05_20261003_3cbf -p 'test_*.py' -v
python -B research/analysis/exogenous_phase_6803_derived_capture_a05_20261003_3cbf/verify_evidence.py
```

The historical freeze commit must be present locally (Actions fetches it
explicitly). Pure construction tests are not additional formal allocations.
Do not invoke runner.py execute again; allocation 02 is consumed. Future native
or live transfer needs a new hypothesis-bearing source-bound experiment, not a
rerun or relabeling of these synthetic artifacts.
