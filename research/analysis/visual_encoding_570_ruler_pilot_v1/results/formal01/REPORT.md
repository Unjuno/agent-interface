# Issue #570 R1 — RAW vs BORDER_RULER

## Disposition

`REJECT_NO_MATERIAL_LOCALIZATION_GAIN` under the preregistered decision rule.
The independently audited result is complete (12 paired cases, 24/24 local
model calls, runner exit 0, auditor `errors=[]`). Preserve RAW as the fallback;
this experiment does not justify promoting ruler annotations.

| Metric | RAW | BORDER_RULER |
|---|---:|---:|
| Positive target hit | 0/10 | 0/10 |
| False selection when target absent | 1/2 | 0/2 |
| Mean normalized center error | 0.1960 | 0.3354 |

Paired mean error improvement (RAW minus ruler) was **-0.1394 screen diagonals**,
so the ruler arm was worse on this metric. The hit counts tied at zero; this is
not evidence that either arm provides useful target localization. The two
absent-target cases are too few for a reliable abstention-rate claim. The
frozen `>=0.02` material-improvement gate was not met.

## Execution and provenance

- Allocation: `visual-ruler-570-r1-20260927-01`; one runner invocation, no
  retries, no tuning, no fine-tuning or optimizer steps.
- Exact frozen model: local Ollama `qwen2.5vl:3b`, digest
  `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`,
  Q4_K_M; Ollama 0.34.4, Python 3.11.9, Pillow 10.4.0.
- 12 synthetic 1280x800 source images (10 target-present, 2 target-absent), each
  evaluated once in each arm. The 24 calls averaged 59.68 seconds each.
- Before inference, `ollama ps` showed no resident model. During/after inference,
  Ollama reported `100% CPU`; `nvidia-smi` remained RTX 3080 Laptop GPU,
  16,384 MiB, 0 MiB used, 0% utilization. This is a local CPU inference result,
  **not GPU evidence**.
- All source/ruler PNGs have identical dimensions. The independent auditor
  verified no differing pixels in the rendered UI region and bound each model
  request to its exact arm-image SHA-256.
- Raw result SHA-256:
  `b53152c981a7647d1aacb45d39a95fbe5b3f74efe09d95950f5c09b90767e313`.
- Independent audit SHA-256:
  `782c9b4fe4be257c3b103980bc196f8f6fc1ccb43f5310068ca58304470b1d72`.

## Interpretation and limits

The frozen small model failed to hit the intended target in either arm; the
ruler did not rescue localization and mean distance worsened. This can reflect
the model, task/prompt, synthetic GUI distribution, or the presentation. The
study does not distinguish those mechanisms. It is a 12-case synthetic screen
on one quantized local CPU backend, not a real-app, GPU, calibration, token-cost,
latency-benefit, action-safety, or general multimodal claim. No input was sent
and no application effect was attempted.

Evidence: `FORMAL_RESULT.json`, append-only `RAW.jsonl`, 24 exact source/arm
PNG files, and independent `AUDIT.json` are retained alongside the frozen
protocol and runner.
