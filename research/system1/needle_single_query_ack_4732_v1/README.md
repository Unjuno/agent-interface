# Needle single-query acknowledgement experiment

Issue #4732; successor to #4714. This experiment tests whether the 512-row held-out batch included in the prior per-feedback acknowledgement path is a harness cost. The formal comparison moves the same full held-out scoring after a one-query durable acknowledgement; it does not remove work or claim improved total throughput.

## Current status

Source and decision gates are published/frozen before the formal run. Construction-v2 on seed 6842783 passed independent audit but showed little latency separation: ack p95 15.590 ms inline-512 vs 15.121 ms one-query (ratio .970). Formal seeds 6842791/93/97 remain untouched at freeze. Construction output and volume are not formal evidence.

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
