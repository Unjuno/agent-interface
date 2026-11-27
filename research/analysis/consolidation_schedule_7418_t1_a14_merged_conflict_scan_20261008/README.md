# T1-A14 merged-memory conflict scan

This one-shot schedule-sensitivity run tests whether an explicit two-pass consolidation instruction improves faithful conflict derivation across a prior/new-memory boundary. It is a synthetic text-only fixture; it does not interact with a GUI, external service, or user data.

A14 is a controlled follow-up to A13. The only intended intervention is in `prompts.json`: after copying prior claims and adding claims for new episodes, the model must rescan every fact observation in the full combined memory and derive any newly applicable conflict. The JSON Schema constraint, fixture, four schedule arms, six checkpoints, five fixed queries, Qwen3:8B digest, generation settings, and independent transition auditor are retained. Seeds are fresh: 5401, 5402, and 5403.

The allocation contains 390 generations (360 query calls and 30 consolidation calls). It is not pooled with any previous allocation. `PROTOCOL.md` records stop/decision rules. `RUN_RECORD.json` records the freeze and one-shot run. Raw responses and independent audit belong in `results/FORMAL_T1_A14/`.

Interpretation gate: schedule contrasts are descriptive only unless the independent auditor reports `PASS_METHOD` with no errors for all 390 rows. A method failure, identity mismatch, missing row, or interrupted request invalidates endpoint interpretation. No call retries or seed replacements are permitted.
