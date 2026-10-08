# Issue #4738 — five-arm synthetic visual-encoding study

This additive successor tests whether deterministic model-facing presentation layers improve Qwen2.5-VL target localization while preserving the raw screenshot as the source of truth. It does not authorize GUI input.

## H / T / D / C / U

- **H:** At least one of `COARSE_GRID`, `CONTEXT_CROP`, or `GRID_CONTEXT` preserves the number of correct present-target detections and absent-target abstentions versus `RAW`, and lowers mean normalized predicted-box-center distance to the target region by at least 0.05 on the fixed 12-screen corpus.
- **T:** 10 positive plus 2 absent synthetic screens; five paired representations per exact screen; 60 fixed calls, temperature 0, same semantic prompt/output schema/model, one local Docker Ollama server, one 200 ms GPU placement sampler. Construction/audit screens use disjoint seeds and zero model calls. No retries.
- **D:** Independent raw audit must show all 60 inputs, prompts, source mappings and results bind exactly; all 60 call intervals must overlap GPU placement above the empty-server baseline. Encoding PASS requires non-decreasing positive hits and absent abstentions plus >=0.05 improvement in mean normalized point-to-region error. Otherwise `REJECT_NO_MATERIAL_ENCODING_GAIN`; integrity/runtime failures remain HOLD/STOP.
- **C:** One Windows RTX 3080 Laptop, Docker Desktop linux/amd64, one cached Ollama 0.34.4 image and Qwen2.5-VL 3B Q4_K_M artifact. Synthetic screens, one seed family, one host; latency is descriptive and no GPU-vs-CPU causal comparison is planned.
- **U:** No real-application transfer, model training, action authority, safety, calibration, human-tempo, generalized GPU benefit or product-readiness claim. A positive proposal result only motivates a separately frozen fresh-admission/effect-scored rung.

## Frozen representations

`RAW` is unchanged. `BORDER_RULER` adds edge ticks/labels. `COARSE_GRID` overlays a sparse 200 px grid. `CONTEXT_CROP` deterministically enlarges a fixed application-body crop without inspecting target identity. `GRID_CONTEXT` provides the same fixed crop with the sparse grid. All five canvas sizes remain 1280x800. Crop arms declare affine mappings back to source coordinates; audit checks the inverse mapping.

## Execution boundary

Pinned images are `ollama/ollama:0.34.4` (`sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551`) and the cached helper (`sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`). Model digest is `fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1`; layer SHA-256 is `e9758e589d443f653821b7be9bb9092c1bf7434522b70ec6e83591b1320fdb4d` (3,200,614,720 bytes). The source and model store are read-only. Ollama has only a Docker internal network, no published port, cloud fallback disabled, and `--gpus all`. The independent auditor runs in a separate network-none, GPU-less helper container.

The Windows Arial font is a local read-only input; only its SHA-256 is published. Exact source images and all five lossless presentation PNGs, source freeze, preformal manifest, raw requests/responses, sampler, logs and audit are retained in this path.
