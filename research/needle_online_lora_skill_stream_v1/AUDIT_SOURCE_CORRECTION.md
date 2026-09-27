# Auditor correction record

The frozen auditor source initially read `fresh_process_wall_ms` from each `worker-NN.json`. The runner intentionally adds that parent-observed value to `orchestration.json`, not to worker metadata. Consequently the first auditor process exited with `KeyError` before making a disposition; it did not alter any evidence or run training.

Correction: `audit.py` now reads `orchestration.json["fresh_process_wall_ms"][arrival-1]`. No training, thresholds, formal inputs, or evidence were changed. The corrected auditor was run in a separate cached-image container with network disabled. It reproduced the uninterrupted training reference and checkpoint states, and returned `FAIL_AUDIT` because strict bit-exact heldout logits and update-only p95 <=60 ms gates failed. See `formal/audit-initial.json` for that complete machine-readable disposition and `REPORT.md` for interpretation.

Frozen pre-correction auditor SHA256: `e7204f3cae30a3afe89a8d25e5bb52930d038747008deb694cfbbc7365b3281b`.
