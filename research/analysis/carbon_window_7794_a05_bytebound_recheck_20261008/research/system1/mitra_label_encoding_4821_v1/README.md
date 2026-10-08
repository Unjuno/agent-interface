# Mitra label-encoding successor — Issue #4821

This package tests the cause of the terminal #4809 STOP without touching its frozen artifacts. The STOP occurred before checkpoint loading because AutoGluon Mitra's stratified split calls `np.bincount(y)`, while the synthetic fixture labels are strings (`C0`…`C5`).

## H / T / D / C / U

- **H:** deterministic contiguous `int64` IDs for frozen vocabulary `C0`…`C5` will let Mitra's support split proceed, and explicit ID→label mapping will preserve the six-column probability ABI in frozen class order.
- **T:** exact 256-row support and 1,024-row query fixtures, model snapshot `edada0d20759c58ada8c8605c25f22f6e98ea5f0`, rev4 offline dependency environment and CUDA image `sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac`. The original #4809 one-shot remains terminal and unchanged.
- **D:** CPU-only Docker construction: 4/4 label/ABI tests pass on the byte-pinned support fixture; an independent stdlib-only auditor passes and rejects 7/7 corruption controls. Integer encoding yields split sizes 204/52 and 204/52 with all six IDs in train+validation. This confirms the preprocessor/split and ABI mapping only; model compatibility remains untested.
- **C:** any formal follow-up is a new allocation with its own freeze, fresh GitHub/task/device/container collision audit, one GPU-requested Docker invocation, independent raw result or STOP audit, no network, and no retries. Do not modify #4809 evidence.
- **U:** one synthetic fixture/model/RTX 3080. No task quality, calibration, safety, cross-host or product claim.

## Reproduction

The construction test command, run in the pinned local image with no GPU request, is:

```powershell
python -m unittest -v test_label_abi
```

Mount this directory read-only as `/src`, its `inputs/` read-only as `/inputs`, and a fresh output directory as `/out`. The separate `audit_diagnostic.py` invocation must use a distinct network-disabled read-only container and output receipt. `FREEZE.json` binds sources, fixtures, model and image; `FORMAL_PROTOCOL.md` defines the one-shot gates.

Construction result: `construction-01/DIAGNOSTIC_RESULT.json`; independent audit: `construction-01/AUDIT.json`. Neither mounted a model or requested CUDA.
