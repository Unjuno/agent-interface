# Mitra inference-mode drift diagnostic — Issue #4947

This is a new allocation after #4935's preserved pre-model STOP. V1's only identified defect was passing the weight file instead of its containing directory as `hf_model`; this package fixes that local path and tests the correction without touching the old branch or outputs.

The experiment reuses the exact #4821 model, class ABI, support/query rows, and rev4 CUDA image. After one context-only fit it records every module's natural `training` state, then compares four matched-RNG repeats on each of the first 16 frozen query rows in natural mode and with `eval()` forced before each call. No optimizer step or task-quality scoring is permitted.

Run `python -m unittest -v test_audit.py` for the synthetic raw-auditor/corruption controls and the static local model-directory argument test. Formal launch and raw-only audit commands, mounts, identities, and gates are fixed in `FORMAL_PROTOCOL.md` and Issue #4947. `runner.py` and `label_abi.py` are byte-identical dependencies from #4821.

## Allocation 01 outcome and publication audit

The sole CUDA-requested container invocation is a terminal STOP at AutoGluon context setup: PyTorch raises `AttributeError: partially initialized module 'torch._dynamo' has no attribute 'external_utils'` while constructing AdamW. The checkpoint did not load; inference count and optimizer updates are zero. This is not a scientific result, and this allocation was not retried. The host-only STOP evidence audit passed.

Post-run review found that the first package file was committed to this branch at 2026-09-27 17:08:02 UTC, after the invocation ended at 17:05:44 UTC. Therefore the preregistered requirement to freeze and read back source from GitHub before the invocation was not met. The package's local source hashes were frozen, but GitHub preregistration was absent at run time. Record this as `STOP_GITHUB_PREREGISTRATION_PROVENANCE`; it further limits the STOP's procedural status and does not change any historical artifact.

The RTX 3080 returned to 0 MiB and the two pre-existing containers were unchanged. See the allocation results directory for the invocation, traceback, STOP, posthoc audits and construction-test receipt. No model-quality or inference-mode conclusion is available.

