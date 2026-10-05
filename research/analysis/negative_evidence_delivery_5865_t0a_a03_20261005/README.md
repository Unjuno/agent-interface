# Issue #5865 T0a A03 — origin-bound negative evidence delivery

Read [PLAN.md](PLAN.md), [CONSTRUCTION.md](CONSTRUCTION.md),
[ENVIRONMENT.md](ENVIRONMENT.md), and the post-run [REPORT.md](REPORT.md).
A03 is a distinct prospective allocation; A01/A02 remain preserved unchanged.

After `FREEZE.json` exists, reproduce from the repository root:

```sh
python3 research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/run_candidate.py \
  --input research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/candidate_input.json \
  --out research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/run-01
python3 research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/audit_result.py \
  --input research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/candidate_input.json \
  --truth research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/oracle_truth.json \
  --events research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/run-01/events.jsonl \
  --results research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/run-01/results.json \
  --out research/analysis/negative_evidence_delivery_5865_t0a_a03_20261005/run-01/independent-audit.json
```

The candidate reads only `candidate_input.json`. `oracle_truth.json` is passed
only to the auditor. The model runs in local Python, not in a container.
