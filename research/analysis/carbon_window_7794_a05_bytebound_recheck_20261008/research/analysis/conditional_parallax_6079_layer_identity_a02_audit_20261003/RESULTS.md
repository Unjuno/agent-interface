# Audit execution record — allocation A02

Status: **HOLD_MUTATION_CONTROL_FAILURE**. One auditor invocation, exit 1, retries 0. Candidate invocation count: 0. No audit JSON was written; do not report PASS_AUDIT_RECONCILED.

Exact command:

```text
python3 audit_successor.py --input ../conditional_parallax_6079_layer_identity_a01_20261003/fixture/public.json --truth ../conditional_parallax_6079_layer_identity_a01_20261003/fixture/auditor_truth.json --raw ../conditional_parallax_6079_layer_identity_a01_20261003/results/formal_01/candidate.raw.jsonl --expected-public-sha256 8614e740c5651471c957ece8df6728f10996e4e24ded12ef2eed21fcf90a45b3 --out results/audit_01/audit.json
```

The stack trace ended with `ValueError: mutation_control_failure`. The auditor's ordinary eight-row reconstruction and truth checks precede that gate, but because the single formal run terminated at the aggregate mutation gate, no PASS is claimed. The exact per-control booleans were not persisted, so the specific failing mutation(s) are unknown. The output path remains absent. This allocation is terminal; do not edit/retry this formal command.

Frozen inputs remain those listed in FREEZE.json. The predecessor #6838 A01 HOLD and raw output are unchanged. Any further work must use a new issue/allocation and independently registered audit criteria/code.
