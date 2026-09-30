# V3 successor: frozen-source and STOP-receipt preservation

Recovery review date: 2026-09-30.

## Disposition

**RETAIN_FROZEN_SOURCE_AND_STOP_RECEIPT_ONLY; HOLD_COMPLETE_EXECUTION_EVIDENCE.** All 11 original [PR #4879](https://github.com/Unjuno/agent-interface/pull/4879) files are preserved byte-for-byte. The original `STOP_OUTPUT_NOT_EMPTY` remains a reported setup STOP before model load, not a precision result. Missing historical stdout, stderr and exit receipts have not been regenerated, inferred from their hashes, or replaced by a rerun.

Source head: `5f10cfba7bcb5ba40c4828ad053161d4424edcda`. Original allocation: `typed-readout-precision-boundary-1014-v3-successor-20260927-01`. Recovery intake main: `b1ffe8f23e74292ee99e44401270bc31438782d3`.

## Independently verified static evidence

Read-only retrieval and byte hashing recreate all 11 original Git blob IDs exactly. All declared byte lengths and SHA-256 values match: 8/8 entries in `SOURCE_MANIFEST.json` and 9/9 entries in `FREEZE.json`. The groups overlap and are not additional allocations or samples. Original CRLF/LF representations are retained unchanged.

The corpus remains exactly 270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. The published source, model-identity manifest, planned commands, tests, and STOP narrative are reachable. External model assets and the declared container image are not bundled or newly downloaded/verified by this review.

Static source inspection places the nonempty-output guard at `run_construction.py` lines 82-83, before input verification, corpus loading, tokenizer loading and model loading. If the reported exception occurred at that guard, those later operations were not reached. CUDA availability/support checks precede the guard; this source ordering is not evidence of a newly observed invocation or a blanket claim that no CUDA initialization occurred.

No repository code, auditor, model, GPU workload, container, GUI action, workflow, or experiment was executed for this recovery review.

## Execution-evidence boundary

`results/STOP_RECORD.md` reports one Docker exit 1, empty stdout with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, and 245-byte stderr with SHA-256 `ff4ddd19f26e779ab8b91829c1c8df24d8d42a46e5cd82677f95ff0dcea59c22`. Neither original log nor a machine-readable invocation/exit receipt is part of this 11-file PR delta. The host wrapper/redirection that reportedly populated `/out` is described, rather than retained as a complete executed command transcript. The model-output directory and post-run GPU state are also reported without separate retained raw snapshots here.

Hash values and a source-consistent explanation cannot reconstruct missing process evidence. Historical no-retry, no-model-forward, idle-GPU and preflight-test statements remain attributed to the original record. Keep the reported STOP and its no-retry boundary; do not promote it to independently re-audited execution or a numerical PASS/FAIL.

## Incremental lineage value

The [v4 protocol](https://github.com/Unjuno/agent-interface/blob/49189c84238a81ba87b3592a86670c7de654a38a/research/system1/typed_readout_precision_boundary_1014_v4/README.md) explicitly identifies #4875's output-directory STOP as its predecessor. The already-main [v5 protocol](../typed_readout_precision_boundary_1014_v5/README.md) then records a distinct successor after v4's omitted-`run` STOP and explicitly separates host logs from model output.

The inspected v4 and v5 manifests retain the same hashes for `audit_raw.py`, `cache_mechanics.py`, `corpus.jsonl`, and `MODEL_MANIFEST.json`, in their own allocation directories. Restoring v3 preserves the original source identity and failure explanation that motivated the subsequent logging/launcher corrections. It does not supply a missing runtime dependency for those self-contained manifest paths, add new precision observations, or pool the allocations.

## H / T / D / C / U

- **H:** Exact frozen source and the original STOP receipt can be retained without inventing absent execution evidence
- **T:** Recompute original blob identities and manifest hashes; inspect source ordering and later lineage; preserve missing-log and process-provenance limits without executing the allocation
- **D:** RETAIN_FROZEN_SOURCE_AND_STOP_RECEIPT_ONLY, with HOLD_COMPLETE_EXECUTION_EVIDENCE unchanged
- **C:** A correct source guard and internally consistent narrative do not independently prove the historical process trace described by that narrative
- **U:** No numerical precision result, model accuracy, formal timing, speedup, task benefit, GPU/host generalization, GUI authority, runtime adoption or product claim. Earlier corpus-identity STOPs and later v4/v5 outcomes remain separate and unchanged

Final-head CI and merged-byte readback are separate integration gates. Preserving the receipt does not complete [Issue #4875](https://github.com/Unjuno/agent-interface/issues/4875)'s original numerical experiment or authorize another attempt.
