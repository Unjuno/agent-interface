# T5 formal disposition — `STOP_AUDIT_MISMATCH`

## Frozen one-shot record

- Intake main: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`.
- Candidate / runner / auditor / fixture freeze: `FREEZE.json`.
- Runtime: CPython 3.14.5, macOS arm64; no Docker/OrbStack action.
- Pre-run construction tests: `python3 -B -m unittest -v test_candidate.py`, exit 0, 5/5.
- Formal command: `python3 -B run_experiment.py`, invoked once, exit 0, 135 rows.
- Raw SHA-256: `469ccc0c4665f0755f40c3d9405577029ea3ae8f00abc9da201478280e9c5bb7`.
- Independent audit command: `python3 -B audit_raw.py`, invoked once after runner exit 0, exit 1.
- Audit disposition: `STOP_AUDIT_MISMATCH`; 54 `declared_spread_mismatch` discrepancies. Five frozen mutation controls were all rejected (5/5).
- Audit receipt SHA-256: `1a09391d0c7d155d0c4961beaeecba6854a8f92f73995702ac9defef2c782cfb`.

## Read-only diagnosis

The independent auditor's fixture table hard-codes `declared_spread=0.5` for `beyond_tolerance`, although the frozen runner declares `0.25`. The runner's value is also the intended preregistered tolerance-boundary case: context spread `0.5`, tolerance `0.25`. This accounts for all 54 audit discrepancies. Raw records retain one consistent declared value per case. No post-run candidate, auditor, raw, or audit edits were made; there was no retry.

Because the audit failed, the scientific gates are not accepted even though this discrepancy appears to be an auditor fixture transcription defect. Preserve this as an audit STOP, not a PASS or FAIL. Any corrected-auditor verification must be a newly frozen successor allocation with a new raw path; this allocation remains immutable.

## Exact frozen source hashes

```
candidate.py       2b5f8a378e7676ba756e2a9e5e0032d4c23c8b112fec5ee605e949ff490d00b7
run_experiment.py  14ddaff104844303c6a8d24d645eabd984f556902ada9612008f4b2279e03918
audit_raw.py       d06ca12d7b58e2fb7a8513b3c8c3ca0bb8eb07eb64ad5c83287f65a8b97ce9e6
test_candidate.py  5bed1120dcac9a1b87ae4e19554b478f39f57d869ef8c7ab94806356ae029416
PLAN.md            4bb8c7516be0811db1343eae9920acde778a8a315e94ec2be19de885b380d8a9
FREEZE.json        779853fcad153b25abbb8781adcca19d63058cb6c17dd3b0352a09379ef4625b
raw/formal.jsonl   469ccc0c4665f0755f40c3d9405577029ea3ae8f00abc9da201478280e9c5bb7
raw/audit.json     1a09391d0c7d155d0c4961beaeecba6854a8f92f73995702ac9defef2c782cfb
```

No conclusion about approximate irreversible admission is accepted from this allocation. No GUI, model, network, external effect, or formal shared-container work occurred.
