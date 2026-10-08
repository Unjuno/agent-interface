# GPU brightness-robust grounding successor (#3682)

This is the frozen local RTX 3080 successor for the CPU RGB-nearest baseline and
the retained 12/18 brightness-robustness STOP. It uses the six manifest-pinned
Chromium source images only, with tasks 1/2/4/5 for training and whole-image
tasks 3/6 held out. Two identical tiny CNNs differ only in training-time
multiplicative brightness augmentation. There is no GUI, model provider, host
IPC, input authority, or task submission.

## H / T / D / C / U

- **H:** Training-only brightness augmentation preserves strict-validator-safe
  layout/coordinate grounding on held-out images under 0.85x/1.15x brightness
  shifts better than the matched no-augmentation CNN.
- **T:** frozen manifest in `research/analysis/local_model_2912_image_manifest.json`;
  train tasks 1,2,4,5; hold out whole source images tasks 3 and 6; evaluate each
  held-out image unchanged and at 0.85x/1.15x (6 rows, 4 perturbed).
- **D:** two matched arms, seed 3682, 200 Adam steps, fixed batch of four,
  64x64 RGB input, CNN 3→8→16→4096→2, Adam lr 0.001. Augmentation uses the
  preregistered alternating 0.85/1.15 factors by step and training-row index.
  Record logits/probabilities, confidence route, mapped coordinates, strict
  validator, runtime/GPU, elapsed time and sampled peak VRAM; independently
  recompute all rows and the decision.
- **C:** no GUI/action/task execution/provider/IPC/authority. Only manifest
  layouts A/B and manifest coordinates are proposed, and every candidate is
  checked by `compiled_form_grounding_v1.validate`. No tuning or data changes.
- **U:** two held-out source images only; repeated brightness variants are not
  independent samples. No unseen-layout, broad robustness, calibration,
  deployment, or product claim.

Docker's local content store returned an I/O error during read-only preflight,
and the host C: volume reported no free space. No Docker state was altered.
The same small model is therefore run directly on this PC's already-installed
CUDA PyTorch 2.5.1+cu121 runtime and RTX 3080 Laptop GPU; there is no external
workflow. Record runtime and source SHA256 pins in `FROZEN_IMAGE.json`, and
commit that freeze before invoking the formal trainer. One allocation only;
retain STOP/HOLD/FAIL and do not retry. The recorded allocation stopped before
the first optimizer step because CUDA deterministic mode required
`CUBLAS_WORKSPACE_CONFIG` before process startup. This frozen run is not
retried, and no model-comparison result is claimed.

## Superseded preallocation note (#3694)

The closed preregistered branch #3694 separately recorded an earlier container
image-pull storage stop before any model process ran; its note is retained in
`PREALLOCATION_CONTAINER_STOP_3694.md`. That branch's proposed local-host
amendment did not become a second allocation: it was superseded before model
execution by the merged allocation documented above. Do not infer another run,
or treat the preallocation note as evidence of training or evaluation.
