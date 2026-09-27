# Mitra inference-mode drift diagnostic — Issue #4947

This is a new allocation after #4935's preserved pre-model STOP. V1's only identified defect was passing the weight file instead of its containing directory as `hf_model`; this package fixes that local path and tests the correction without touching the old branch or outputs.

The experiment reuses the exact #4821 model, class ABI, support/query rows, and rev4 CUDA image. After one context-only fit it records every module's natural `training` state, then compares four matched-RNG repeats on each of the first 16 frozen query rows in natural mode and with `eval()` forced before each call. No optimizer step or task-quality scoring is permitted.

Run `python -m unittest -v test_audit.py` for the synthetic raw-auditor/corruption controls and the static local model-directory argument test. Formal launch and raw-only audit commands, mounts, identities, and gates are fixed in `FORMAL_PROTOCOL.md` and Issue #4947. `runner.py` and `label_abi.py` are byte-identical dependencies from #4821.

