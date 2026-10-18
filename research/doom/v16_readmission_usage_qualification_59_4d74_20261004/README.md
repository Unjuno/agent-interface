# V16 readmission usage-snapshot qualification

This additive auditor repairs the reproducibility gap reported on Issue #59 after the visual04 archive merged. It reads the committed `run/episode/report.json` and `run/host.stdout.jsonl` files. The original `run/SAVED_READMISSION_AUDIT.json`, `run/USAGE_QUALIFICATION.json`, and `audit_visual_04.py` remain untouched.

## H/T/D/C/U

- **H:** The first auditor counted all six turn-identified `last` snapshots as known completed usage, including two interrupted turns whose notifications repeat the preceding completed snapshot. The checked-in first auditor also points to an unpublished `controller-visual-04/` staging directory rather than the committed `run/` path.
- **T:** Reconcile each report decision with the latest host `thread/tokenUsage/updated` notification for the report's app-server thread and exact turn ID. Include only turns explicitly marked completed in the descriptive sum of observed `last` snapshots. Scan retained JSON/JSONL for response-level usage records.
- **D:** PASS snapshot reconciliation only when all report usage snapshots match the matching latest host notification and no malformed/missing/duplicate records affect the join. Always HOLD full-attempt usage interpretation because these snapshots do not establish response-level completeness; interrupted-turn increments remain UNKNOWN.
- **C:** Turn IDs route notification snapshots; they do not make `last` a per-turn delta. A repeated or unchanged snapshot does not prove zero interrupted-turn cost. A completed turn's `last` can also omit earlier responses in a multi-response turn.
- **U:** This is archived-data accounting only. It makes no billing claim, no runtime/model/game/input claim, and no claim of complete attempted usage.

## Reproduce

From the repository root:

```powershell
python research/doom/v16_readmission_usage_qualification_59_4d74_20261004/audit_usage_qualification.py
python -m unittest research.doom.v16_readmission_usage_qualification_59_4d74_20261004.test_usage_qualification
python research/doom/v16_readmission_usage_qualification_59_4d74_20261004/audit_qualified_usage.py
```

The qualified result is written to `QUALIFIED_USAGE.json` in this directory. Expected observed completed-turn `last` snapshot sum: 48,773 input / 1,100 output. Two interrupted turns remain UNKNOWN for incremental usage; no response-level usage records are retained in the archived JSON artifacts, so full-attempt usage remains NOT_ESTABLISHED.

This package is a successor interpretation. It does not rewrite the first auditor's 71,597 / 1,724 claim or its additive correction; it labels the first value as the preserved erroneous claim and emits a corrected status-aware result separately.
