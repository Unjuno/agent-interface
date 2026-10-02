# Issue #6616 — history-conditioned reliance T0 A03

This additive allocation executes the no-participant stimulus/scorer construction proposed in Issue #6616. It is distinct from the earlier lifecycle/provenance package under `history_receipt_provenance_6616_*`; those STOP/HOLD outcomes remain immutable.

See `PREREGISTRATION.md` for H/T/D/C/U and the frozen factorial design, `FREEZE.json` for source/environment identities, `RUN_RECORD.md` for exact one-shot execution receipts, and `REPORT.md` for the bounded result. The output is a synthetic stimulus construction only. It cannot establish that outcome order changes human behavior. Issue-level T0 remains on hold until two independent reviewers complete `REVIEW_PROTOCOL.md` against the separately emitted blinded packets.

Reproduce the local contract suite with:

```sh
python -B -m unittest discover -s research/analysis/history_conditioned_reliance_6616_t0_a03_orbstack_20261003 -p 'test_*.py' -v
```
