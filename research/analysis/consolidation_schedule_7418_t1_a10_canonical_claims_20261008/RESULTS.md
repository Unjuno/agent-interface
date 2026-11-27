# A10 results — FAIL_METHOD

The frozen candidate completed the single authorized run: 390/390 model calls, exit 0, no retries. The frozen raw-only auditor completed once, exit 0 as a process, and returned `FAIL_METHOD` with 54 transition errors. The protocol's method gate failed, so the cadence endpoint is not interpretable as a research result.

The errors recur across all three seeds and include:

- The exception episode was stored as `rare_exception` instead of the required canonical `forbidden_effect_exception`.
- Fact claims used the literal field name `fact_key` as their key instead of the observed key.
- History claims used only the paired field name, omitting its version-derived key.
- Several terminal/per-episode states had bad or unknown source provenance.
- Terminal states asserted the wrong exact effect for the exception, and batch-2 emitted a conflict claim inconsistent with the scoped-conflict contract.

Answer accuracy was identical by arm across seeds: episodic-only 0.2667, per-episode 0.5333, batch-2 0.5333, terminal 0.6667. The auditor listed five consistent contrasts of at least 0.10. These are descriptive only: because the preregistered transition gate failed, they do not establish schedule sensitivity under faithful memory transitions and are not eligible for endpoint interpretation.

## Preserved artifacts

- Raw: `results/FORMAL_T1_A10/RAW.jsonl`, 1,930,469 bytes, SHA-256 `9736080c6ad3b86e3d1377d2b5ec38b9759a03c86327aad0a1497f61f42ae2c3`.
- Audit: `results/FORMAL_T1_A10/AUDIT.json`, 13,121 bytes, SHA-256 `20ed2a53238a60acc603bdb591aa2830eb64cb607e7384757d86e50d0477f327`.
- Candidate stdout/stderr and auditor stdout/stderr are preserved beside them. Stderr was empty for both processes.

The frozen source, prompt, input, seed, model and audit artifacts remain unchanged. This allocation will not be rerun or repaired. A successor, if run, requires a fresh allocation and fresh seeds.
