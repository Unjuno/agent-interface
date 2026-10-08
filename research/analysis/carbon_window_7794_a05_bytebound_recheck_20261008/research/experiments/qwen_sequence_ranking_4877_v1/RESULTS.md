# Formal result — Issue #4877

Status: **PASS under the narrow preregistered synthetic criterion**. This is not evidence of real-world intent quality or deployment readiness.

- Fresh held-out synthetic set: 32 rows, seed 4792963; input SHA-256 `08070317f893fb443bf601de5c882da29df7868764fd9fe98a2d56cf77566cc0`.
- Exact recovered #4792 LoRA adapter; Qwen2.5-0.5B-Instruct snapshot `7ae557604adf67be50417f59c2c2f167def9a775`; CPU-only, offline Docker image SHA-256 `63ce8205b5e0cf7daddac087d6c1bd5489d51e3af345cf923af925026bdd600c`; no optimizer updates or training.
- Free greedy: 11/32 exact (34.4%), 11/32 BOUND, 21 REJECT, zero disallowed simulated effects.
- State-trie greedy: 5/32 exact (15.6%), 4/32 BOUND, 13 NO_ACTION, 15 REJECT, zero disallowed effects.
- Full-candidate conditional log-likelihood ranking (sum of candidate token log-probabilities including EOS, no length normalization): **20/32 exact (62.5%)**, 16/32 BOUND, 8 YIELD, 8 REJECT, zero disallowed effects. Relative to trie: +15 exact rows (+46.9 percentage points), +12 BOUND rows. It meets the issue threshold (>=16 exact and >=20pp gain over trie), but is below free generation by 2 exact rows; do not conclude broad superiority.
- Cost: 64 generation calls, 296 candidate scoring passes. This small CPU experiment required several minutes for inference and a second full scoring pass for audit; score ranking is not cheap under this straightforward implementation.
- Independent audit recomputed all 296 candidate sums and rankings, verified candidate-set membership, binder/effects and all six corruption controls: PASS. Audit input/raw SHA-256s match above and raw SHA-256 `632de50cf8d637feea9ab83542c6993a293f56cdab1a70a1caee609eb5529da2`.
- No candidate in this synthetic set caused a disallowed or mismatched simulator effect after binding. This does not establish safety outside the frozen authority-neutral simulator.

## Interpretation

Whole-candidate scoring substantially beats token-trie greedy on this narrow constructed set. Trie-greedy's local token choice often commits to the wrong complete candidate; scoring complete state-derived candidates changes the selected path. However, full-sequence ranking does not beat unconstrained greedy here (20 vs 11 only? It does beat it by 9 rows); the frozen data gives 20 vs 11, a +28.1pp improvement. Report only this measured comparison, and note synthetic distribution limitations. No fine-tuning, benchmark transfer, live UI, persistence, or agent tool integration was tested.

## Reproducibility and deviations

Source and execution freezes are adjacent JSON records. Raw full per-row outputs/scores are stored locally at `work/qwen_sequence_ranking_4877_v1/attempt_02/raw.json` (262,931 bytes, SHA above); the dataset at `work/qwen_sequence_ranking_4877_v1/results/input.json` (69,415 bytes, SHA above). GitHub source records the exact hashes and commands; raw is also present as a base64-encoded artifact under `artifacts/raw.json.base64` for transport-safe exact reconstruction.

Two non-model execution/audit failures are preserved: attempt 01 completed model computation but output mount was read-only, so no raw was persisted; attempt 02's first audit exposed an insensitive ranking-score corruption control. Neither is silently overwritten. The corrected auditor was frozen by hash before its passing rerun on the unchanged raw. These failures do not count as additional formal inference runs.
