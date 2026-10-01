# Issue #4728 — local Qwen2.5-VL GPU localization result

## H — hypothesis and outcome

On this Windows x64 PC, the exact cached Qwen2.5-VL 3B Q4_K_M model could be loaded by pinned Ollama 0.34.4 in an isolated Docker Desktop linux/amd64 container with RTX 3080 offload, and could localize a sole synthetic blue Apply button on >=5/6 panels while abstaining on 2/2 absent controls.

**Outcome: `PASS_DIAGNOSTIC_SCOPED`.** The independently audited fixed block achieved 6/6 positive detections at IoU >=0.5 and 2/2 correct absent-target abstentions. Every formal request interval overlaps multiple positive GPU/offload samples above the empty-server baseline. Independent audit errors are empty.

## T — frozen and executed test

The source freeze and its SHA sidecar were committed before model requests. The generator created six positive 1280x800 layouts, two absent controls and a separate lower-right construction case. `PREFORMAL.json`, its SHA sidecar, and all nine PNGs (lossless base64 text transport) were committed to the new branch and read back byte-for-byte before inference. Source code was not changed after freeze.

The inference service used local image ID `sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551`, model tag `qwen2.5vl:3b`, API digest `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`, Q4_K_M, and model-layer SHA-256 `e9758e589d443f653821b7be9bb9092c1bf7434522b70ec6e83591b1320fdb4d` (3,200,614,720 bytes). The Python/PyTorch/Pillow helper used pinned image `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261` without a GPU device request. The model store and source were read-only; the internal Docker network had no egress and no published port.

Empty-server baseline was 0 MiB / 0% GPU with `ollama ps` empty. One separate off-center construction request passed the GPU gate: 76 positive placement samples in its call interval (169 total samples during the cold-start interval). The formal block then issued exactly eight calls, temperature 0, fixed row seeds, with no retry or replacement. GPU sampler cadence was 200 ms. Formal VRAM peak observed by `nvidia-smi` was 4,481 MiB; Ollama reported `100% GPU` placement.

## D — raw result and decision

| Case | Expected | Model result | IoU | Positive GPU samples in call |
|---|---|---|---:|---:|
| positive-01 | Apply present | box returned | 0.8859 | 4 |
| positive-02 | Apply present | box returned | 0.8864 | 3 |
| positive-03 | Apply present | box returned | 0.8403 | 3 |
| positive-04 | Apply present | box returned | 0.8403 | 3 |
| positive-05 | Apply present | box returned | 0.8864 | 3 |
| positive-06 | Apply present | box returned | 0.8565 | 3 |
| absent-01 | no Apply | `present=false`, `box=null` | — | 3 |
| absent-02 | no Apply | `present=false`, `box=null` | — | 2 |

All eight request/image/prompt/seed bindings passed. All eight request intervals had placement evidence. The frozen raw-only auditor, run separately in the pinned helper container with `--network none` and no GPU, returned `PASS_DIAGNOSTIC_SCOPED`, 6/6 positive hits, 2/2 abstentions, `errors=[]`. Four adversarial/unit checks passed both on host and in the pinned helper. Warm-call wall times were 1,573–2,122 ms (median 1,766 ms; nearest-rank p95 2,122 ms), descriptive only and not a gate.

## C — confounders and preserved failures

An independent CPU-only formal container was active during the run; Docker inspection showed no GPU device request. It could affect latency/thermal conditions, so no latency comparison or causal GPU benefit is claimed. It did not prevent direct GPU-placement proof. No other GPU allocation was observed. The earlier ARM64/OrbStack STOP in #4719 and merged PR #4722 remain unchanged.

Two execution-tool failures are preserved rather than hidden: an initial helper test command attempted bytecode writes into the intentionally read-only source mount (exit 1 before tests); the corrected no-bytecode command passed 4/4. After all eight model responses and sampler data had been written, `launch.py` exited 1 while decoding Ollama logs using the Windows cp932 default, before its embedded auditor/stop step. No model request was repeated. Logs were recovered with direct file redirection, an independent helper-container raw audit passed, and only the exact R4 Ollama container created by this allocation was stopped. Details are retained in `PREFLIGHT.json` and `POSTRUN_FAILURE.json`.

## U — limits

This establishes one host's local Docker GPU/model availability and easy synthetic label localization only. It does not test the visual ruler/grid/context treatment contrast, real applications, held-out UI families, safety, calibration, action authority, model training, general GPU benefit, or product readiness. Keep #570 and #4719 open; do not generalize this result to all visual inputs.

## Reproduction and integration

The executable source freeze, image/model identities, PREFORMAL, screen bundle, raw construction/formal calls, sampler, baseline, logs, audit and evidence hashes are under `research/analysis/visual_encoding_570_gpu_local_successor_v1/`. Do not rerun this consumed allocation. Any further test needs a distinct successor issue and fresh allocation.

Post-formal publication-byte verification and the corrected, separately versioned auditor are documented in [`postformal/REPORT.md`](postformal/REPORT.md). They preserve this frozen report, v1 sources, and raw evidence; no model requests were repeated.

