# Mitra inference-mode drift diagnostic — Issue #4935

This is an additive, single-allocation follow-up to the terminal #4821 CUDA STOP. It asks whether the retained classifier's module mode explains repeated probability drift. It does not retry #4821 or qualify inference quality, timing, or product readiness.

The probe reuses the exact #4821 model, class ABI, support rows, query rows, and rev4 CUDA image. After one context-only fit it snapshots each module's natural `training` flag. For each of the first 16 frozen queries it performs four matched RNG-state repetitions in arm A (restored natural mode) and arm B (`eval()` called before each query). It records full probability vectors and module flags immediately before and after every call. No optimizer step or parameter update is permitted.

Run `python -m unittest -v test_audit.py` locally for the synthetic raw-auditor/corruption controls. Formal GPU runner and independent CPU auditor commands, mounts, identities and gates are fixed in `FORMAL_PROTOCOL.md` and Issue #4935. Formal launch remains prohibited while another active local timing allocation uses Docker/CPU/GPU.

The exact #4821 `runner.py` and `label_abi.py` are retained byte-for-byte as read-only dependencies; this probe imports only their contract loader, direct classifier, resource instrumentation and CUDA prediction recorder.
