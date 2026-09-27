# Issue #4850 CUDA extent-readout construction result

## H / T / D / C / U

**H.** The #4837 tiny shared CNN's max+mean global pooling may recover construction competence on fixed synthetic data; max-only is the matched control.

**T.** One construction invocation on RTX 3080 Laptop GPU using pinned `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, linux/amd64. Container: network none, read-only root/source, one CPU, 2 GiB, 64 PIDs; `CUBLAS_WORKSPACE_CONFIG=:4096:8` set inside container; deterministic algorithms enabled, cuDNN deterministic, TF32 disabled. Exact command used the frozen runner in this directory. The prefit 49-parameter finite-difference check passed (max symmetric relative error 4.588699537529518e-7). Two arms ran exactly 1,000 SGD updates each at LR 0.2, seed 89100471 / init 89100472. Formal fits: 0.

**D — decision.** The frozen raw-only CPU direct-loop audit reconstructs all 20 arm×split logits with errors=[]. Its scientific score is `STOP_NO_CONSTRUCTION_COMPETENCE`: max+mean train/base accuracy 0.50/0.50, mean held-out positive ACCEPT 0.00, held-out negative false ACCEPT 0.00; max-only held-out positive ACCEPT 0.00. The predeclared 8 mutation controls were then run against a disposable copy of the retained result: only 5/8 were rejected. Changes to data seed, negative fit time and source-hash field were accepted. Because 8/8 was a required audit gate, the overall publication disposition is `HOLD_AUDIT_MUTATION_CONTROLS_5_OF_8`, not a clean construction PASS or a fully accepted scientific STOP.

**C.** This is a device/framework-image placement change from #4837's NumPy/OpenBLAS CPU implementation. CUDA arithmetic may differ. No causal GPU-vs-CPU quality or speed claim. No predecessor result was modified. One synthetic seed and one local device.

**U.** No efficacy/generalization or real-app claim. The 3,942,316-byte `INPUTS.npz` is retained locally at `C:\Users\junny\AppData\Local\Temp\aiface-4850-cuda-v3\out\result\INPUTS.npz`, SHA-256 `624e57e64da36a9e4f6ace4187b71d737630523dee90b7b697d97a05e7127fa5`; this large generated input file is not yet committed in this PR. The frozen seed generator and input hash permit reconstruction/checking, but public self-contained raw replay remains incomplete until those exact bytes or a validated regeneration receipt are integrated.

## Environment and resource receipts

- Python `3.11.10`, PyTorch `2.5.1+cu121`, CUDA `12.1`, NumPy `2.1.2`.
- Peak CUDA allocated: 82,928,128 bytes.
- Fit times (descriptive only): max-only 1.204 s, max+mean 1.175 s.
- Full pre-run GPU XML snapshot remains local; SHA-256 `7fa754f9a2d29b4c1a81e961df3d99cb98868605fde7258a0a78420d7cea46c0`.
