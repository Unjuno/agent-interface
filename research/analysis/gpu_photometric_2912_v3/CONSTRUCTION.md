# Excluded construction record — Issue #4470

Date: 2026-09-26 JST. Intake main: `9e3ee7ea02b27e935a50130a0be45e9938a4dfdb`.

## Environment

- Windows host Python 3.11.9; PyTorch 2.5.1+cu121; CUDA 12.1.
- NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB. GPU was idle before the probe.
- `CUBLAS_WORKSPACE_CONFIG=:4096:8`; deterministic algorithms enabled; TF32 disabled.
- C: had 323,106,394,112 bytes free before construction; the formal preflight later measured 314,485,723,136 bytes free.
- No CUDA-enabled PyTorch image is cached. The cached CPU model image has no PyTorch install. No image pull or package install was attempted.

## Fixed-pool probe

Input: a deterministic random CUDA tensor shaped `[16,16,40,25]`; fixed height/width averaging matrices construct an `[16,16,8,10]` result. The reference is CPU PyTorch `adaptive_avg_pool2d((8,10))` over the same FP32 input. A fixed nonuniform output weight generated a scalar backward objective. The CUDA forward/backward was repeated twice with fresh cloned inputs.

Observed: output shape `[16,16,8,10]`; maximum absolute difference from the CPU reference `1.7881393432617188e-07` (gate `<=1e-6`); repeated outputs bit-identical; repeated input gradients bit-identical. No deterministic-algorithm exception.

## Construction controls

`test_construction.py` ran once on the host with the pre-start CUBLAS setting: 4/4 tests passed. It verified canonical manifest digest, all six exact PNG hashes, CPU pooling equivalence, both compiled-layout candidates accepted, an out-of-bounds candidate rejected, and repeated deterministic CUDA forward/backward. `test_audit_controls.py` passed 4/4 tests: a clean synthetic result audited to HOLD, all 17 individually corrupted variants rejected, an aggregate gain with one perturbed-case regression remained HOLD, and accepted wrong coordinates produced FAIL. The effective per-case gate is reconstructed from each task/transform row, not aggregate transform counts.

### Pre-freeze control failures and corrections

Construction-only auditor iterations were not formal allocations. The first control run raised `KeyError: 'accept'` because route outcomes used `accept` while the summary counter was named `accepted`; the counters now map each route explicitly. The next clean-fixture check falsely classified correct candidates because the auditor compared the validator's full return object (including its method declaration) with a two-coordinate object; it now compares the field and submit points separately. The per-case mutation then showed that transform-level counts had been reused for each held-out image; the frozen gate now records each `(task, transform)` exactness independently. One intermediate synthetic control fixture also had the same overbroad dictionary comparison and was corrected. After these fixes, all final frozen controls passed as summarized above.

## Formal allocation STOP

The sole preregistered allocation was invoked once on 2026-09-26 at 14:02:27 UTC on the same host. Preflight observed 314,485,723,136 bytes free on C: and 16,167 MiB free of 16,384 MiB GPU memory; the frozen commit and `FREEZE.json` digest matched the published allocation. The runner exited with code 1 at 14:02:33 UTC, before an optimizer step, when the CNN produced a feature map shaped `(25, 40)` but the fixed-pooling module required `(40, 25)`. No `results.json`, held-out predictions, metric, or augmentation comparison exists. This allocation is STOPPED and must not be retried or patched in place.

Retained process evidence under `results/formal01/`: `FORMAL_METADATA.json`, `PROCESS_EXIT.json`, empty `runner.stdout.log`, and `runner.stderr.log`. SHA-256 respectively: `b4c53654f3c4896b41448065395fd7c9ebb4fd5600221853fdcd088441e58f46`, `3c480c0591f476e2e50d0845f790b702ffc29b88ff93b36f45b870bb2d08c15a`, `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, and `621b85e494eba1e364025d2ecb517049564beb3885fc3291c8dca4a6e4e37658`. GitHub Issue #4470 records STOP. This failure identifies a missing construction control only; it gives no evidence for or against the augmentation hypothesis. A distinct successor must bind pooling dimensions to the actual CNN output and assert the end-to-end CNN shape on CPU before any formal GPU allocation.
