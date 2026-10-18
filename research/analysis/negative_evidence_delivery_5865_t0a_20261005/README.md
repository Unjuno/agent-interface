# Issue #5865 T0a — origin-bound negative evidence delivery

Read [PLAN.md](PLAN.md), [ENVIRONMENT.md](ENVIRONMENT.md), and
[REPORT.md](REPORT.md) for the frozen question, execution limits, and result.
The candidate reads only `candidate_input.json`; hidden ground truth is kept in
`oracle_truth.json` for the independent audit.

From the repository root:

```sh
python3 research/analysis/negative_evidence_delivery_5865_t0a_20261005/run_candidate.py \
  --input research/analysis/negative_evidence_delivery_5865_t0a_20261005/candidate_input.json \
  --out research/analysis/negative_evidence_delivery_5865_t0a_20261005/run-01
python3 research/analysis/negative_evidence_delivery_5865_t0a_20261005/audit_result.py \
  --input research/analysis/negative_evidence_delivery_5865_t0a_20261005/candidate_input.json \
  --truth research/analysis/negative_evidence_delivery_5865_t0a_20261005/oracle_truth.json \
  --events research/analysis/negative_evidence_delivery_5865_t0a_20261005/run-01/events.jsonl \
  --results research/analysis/negative_evidence_delivery_5865_t0a_20261005/run-01/results.json \
  --out research/analysis/negative_evidence_delivery_5865_t0a_20261005/run-01/independent-audit.json
```

The candidate and audit are separate programs. `FREEZE.json` records the
pre-run identities; `run-01` is the first and only candidate output.
