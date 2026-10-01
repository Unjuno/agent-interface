# Post-run disposition amendment and coordination record

This is an additive correction to the result record. The frozen runner and raw observed aggregates are unchanged; no formal allocation was repeated.

## Pre-allocation issue clarification

Issue #3701 comment [5751335103](https://github.com/Unjuno/agent-interface/issues/3701#issuecomment-5751335103), posted before the GPU allocation, clarified that a scoped PASS also required at least one shared-control B/C held-out accuracy below 0.90, and required tensor-by-tensor comparisons for every state_dict tensor. The observed shared-control scores satisfy the interference discriminator (B=0.0007; C=0.9370). However, the frozen runner's snapshot payload contains only trainable adapter tensors `a` and `b`; it compares those exactly and separately verifies the shared base remains unchanged, but does not round-trip every tensor in the full LoRA module state_dict. Therefore the pre-allocation exact-state condition is not established, and the disposition is corrected to `HOLD_PROTOCOL_DEVIATION`, not PASS.

The result auditor is a structural/result-shape audit only. It checks frozen source identity and recorded fields/gates; it does not regenerate the synthetic data or independently recompute accuracies. Per-row predictions/logits were not retained. The accuracy figures remain the contemporaneous runner output and are not independently reproducible from this artifact.

The issue's D list also requested isolated adapter setup timing. The runner records training/update timing but not construction-only setup duration. Each adapter's trainable parameter count (40) is derived from the frozen shapes. The omission remains explicit; no number is inferred.

## Concurrent branch attempt

The other issue branch `research/needle-lora-3441-pilot-04-multiskill` later recorded `STOP_FORMAL_CUBLAS_DETERMINISM_CONFIGURATION` at commit `921b27af794d32ad76872896f1999b9525bc749a`, before any optimizer step. Its STOP record remains untouched. This branch's one host allocation did run to completion with `CUBLAS_WORKSPACE_CONFIG=:4096:8`, but the two-branch coordination overlap means it should not be treated as the canonical completion of Issue #3701. The evidence is retained as a separate supplemental run and review is required before any integration claim.

Docker remained unavailable; this supplemental allocation used the explicitly allowed local RTX 3080 host path and is not a container result.
