# Issue #4850 CUDA extent-readout construction result

## H / T / D / C / U

**H.** The #4837 tiny shared CNN's max+mean global pooling may recover construction competence on fixed synthetic data; max-only is the matched control.

**T.** One construction invocation on RTX 3080 Laptop GPU using pinned `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, linux/amd64. Container: network none, read-only root/source, one CPU, 2 GiB, 64 PIDs; `CUBLAS_WORKSPACE_CONFIG=:4096:8` set inside container; deterministic algorithms enabled, cuDNN deterministic, TF32 disabled. The prefit 49-parameter finite-difference check passed (max symmetric relative error 4.588699537529518e-7). Two arms ran exactly 1,000 SGD updates each at LR 0.2, seed 89100471 / init 89100472. Formal fits: 0.

**D - decision.** The original frozen CPU direct-loop audit reconstructed all 20 arm/split logits with `errors=[]`. Scientific result: `STOP_NO_CONSTRUCTION_COMPETENCE`: max+mean train/base accuracy 0.50/0.50, mean held-out positive ACCEPT 0.00, held-out negative false ACCEPT 0.00; max-only held positive ACCEPT 0.00. The original 8 mutation controls rejected 5/8; this original outcome remains retained unchanged.

A separately versioned, CPU-only posthoc v2 audit regenerated `INPUTS.npz` under NumPy 2.1.2 and reproduced its 3,942,316 bytes and SHA-256 `624e57e64da36a9e4f6ace4187b71d737630523dee90b7b697d97a05e7127fa5` byte-for-byte against the retained input; it also reproduced the original audit JSON. Its eight distinct mutation cases rejected 8/8. See `out/result/AUDIT_V2.json`, `CONTROL_RESULTS_V2.json`, and `REGENERATION_RECEIPT.json`. V2 is CPU-only and separate: it does not change the negative scientific result or replace the original 5/8 record. The v2 audit and control scripts, runner, raw bytes, initial/final weights, and their hashes are listed in `src/POSTHOC_MANIFEST.json`.

**C.** This is a device/framework-image placement change from #4837's NumPy/OpenBLAS CPU implementation. CUDA arithmetic may differ. No causal GPU-vs-CPU quality or speed claim. No predecessor result was modified. One synthetic seed and one local device.

**U.** No efficacy/generalization or real-app claim. This PR provides a validated regeneration receipt instead of committing the 3.94 MB generated input. `rebuild_inputs.py` reproduces the compressed bytes in the pinned NumPy 2.1.2 container; `audit_cpu_v2.py` directly audits against the regenerated temporary input and verifies any retained copy byte-for-byte. The exact input hash, regenerator and v2 checks are public and reproducible. Full pre-run GPU XML remains local; SHA-256 `7fa754f9a2d29b4c1a81e961df3d99cb98868605fde7258a0a78420d7cea46c0`.

## Environment and resource receipts

- Python `3.11.10`, PyTorch `2.5.1+cu121`, CUDA `12.1`, NumPy `2.1.2`.
- Peak CUDA allocated: 82,928,128 bytes.
- Fit times (descriptive only): max-only 1.204 s, max+mean 1.175 s.

