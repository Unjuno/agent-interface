# Issue #4561 preregistration — fixed-pool template-diversity grounding

**Status: FROZEN BEFORE THE FORMAL TRAINING INVOCATION.** This is a synthetic, local-only model experiment. It does not authorize GUI interaction, remote inference/training, or runtime promotion.

## H / T / D / C / U

- **H:** at equal image/update budgets, training the same compact coordinate grounder on eight distinct synthetic form-geometry families rather than two will improve exact paired field-and-submit localization on four wholly held-out geometry families.
- **T:** deterministic Pillow 10.2.0 raster corpus: 12 source-geometry families × 4 fixed content/theme variants. Families 01–08 are the broad training set; families 09–12 are held out whole. The narrow arm uses only families 01–02. Each arm uses seeds 456101, 456102, 456103, 400 Adam updates, batch 16, learning rate 0.001, and identical samples/update count. Two 8×10 heatmaps predict field and submit cells. Labels map cells through the frozen fixed-pool footprint centers into 1280×800 source coordinates; output is passed through the unchanged strict `compiled-form-grounding-v1` validator. Accept only when both softmax maxima are at least 0.75; otherwise yield/no candidate.
- **D:** one invocation, six independently trained seed×arm models, 2,400 optimizer steps total, 96 held-out cases. PASS only if broad accuracy is ≥0.90 on each held-out family, broad aggregate exact-pair accuracy exceeds narrow by ≥0.10, and accepted wrong-coordinate candidates equal zero. Any integrity violation is FAIL; valid but unmet scientific gates are HOLD/FAIL. No retries, tuning, or substitution after formal starts.
- **C:** #4546's earlier STOP was caused by nondeterministic `adaptive_avg_pool2d` backward under strict CUDA settings and therefore produced no scientific evidence. The successor uses the already-reviewed deterministic fixed-matrix pooling from #4482; it is tested against the CPU adaptive-pool oracle and for bitwise CUDA forward/input-gradient repeatability before training. No pretrained weights or external data are used. Narrow/broad differ only in the allowed training-family population; held-out templates and validation are identical.
- **U:** renderer/template distribution is synthetic and deliberately small; success would establish only this bounded family-diversity result, not real GUI grounding or generalization to arbitrary websites. A single local GPU and three seeds do not establish production reliability. Styling/content variants do not add geometry families. Threshold calibration is not claimed.

## Frozen source and runtime

- GitHub main base at freeze: `0751862d732f4aec0e4149f7f47131edb310f1e9`.
- Source path: `research/analysis/gpu_grounding_template_diversity_2912_v2/`.
- Exact source files and `corpus_manifest.json` are individually committed/read back before formal execution; the pre-rendered corpus manifest SHA-256 is `7e4958551a229d75ba8da8fe23fb47b7c013d3228a7c6aabf745848b5004c9f7`. It fixes all 48 raster PNG and pixel hashes, family/source hashes and coordinate labels before any training. `FREEZE.json` records source blob IDs and SHA-256 digests.
- Container: existing `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, Pillow 10.2.0; verified CUDA device `NVIDIA GeForce RTX 3080 Laptop GPU`. Corpus/results are written to a dedicated host bind mount; source is read-only in the construction test. No network is required.
- Determinism: `CUBLAS_WORKSPACE_CONFIG=:4096:8`, deterministic algorithms and cuDNN, benchmark and TF32 disabled.

## Invocation boundary

Construction/unit tests and the synthetic auditor fixture are not optimizer training runs. Formal is permitted exactly once after exact GitHub source readback, construction gates, deterministic CUDA test and auditor mutation controls pass. Formal outputs are retained verbatim; the independent audit runs only after the one formal invocation and cannot trigger a rerun.
