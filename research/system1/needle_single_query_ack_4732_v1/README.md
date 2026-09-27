# Needle single-query acknowledgement experiment

Issue #4732; successor to #4714. This experiment tests whether the 512-row held-out batch included in the prior per-feedback acknowledgement path is a harness cost. The formal comparison moves the same full held-out scoring after a one-query durable acknowledgement; it does not remove work or claim improved total throughput.

## Current status

The frozen formal trainer ran once on seeds 6842791/93/97; the frozen independent auditor ran once and stopped with `KeyError` due to a stale summary field. Disposition: `STOP_AUDITOR_IMPLEMENTATION_DEFECT`, with no scientific verdict and no retry. All six raw trainer/input JSON files and `formal/FORMAL_STOP.json` are retained below. The prior construction-v2 result remains separate and unchanged.

## Files

- `PREREGISTRATION.md`: H/T/D/C/U and fixed decision rule.
- `runner.py`: experiment runner; imports predecessor model/data code read-only from `../needle_native_volume_checkpoint_4714_v1/src/study.py` at the recorded digest.
- `audit.py`: separate replay auditor; does not import the runner.
- `test_study.py`: construction contract tests.
- `FREEZE.json`: source, image, branch, volume, command and output identity.
- `CONSTRUCTION_HISTORY.md`: append-only construction chronology, including the preserved first run and correction.
- `CONSTRUCTION_MANIFEST.json`: byte lengths and SHA-256 for all retained construction raw runs, inputs and independent audits.
- `formal/`: one-shot raw results, independent report, final snapshots and command logs after formal execution.

No runtime behavior or product authority is changed. Synthetic local Docker evidence only.
