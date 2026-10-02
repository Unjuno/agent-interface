# Issue #2031 T1 — frozen local model-utility allocation

Allocation: `issue2031-gemma3gpu-t1-20261002-01`
Branch: `research/model-localization-2031-gemma3gpu-t1-20261002-0e817b2`
Base: `0e817b20eb721f9f0b3a063016f95951ac52d6a6`

Parent Issue: [#2031](https://github.com/Unjuno/agent-interface/issues/2031)
Concise result: [REPORT.md](REPORT.md)

## H — hypothesis

On this fixed synthetic GUI task family and one local multimodal model, overview plus a truth-independent deterministic candidate crop may preserve or improve source-coordinate target localization versus full-resolution input while reducing actual model-facing input burden. Missing-target crops and absent/ambiguous targets may instead increase errors.

## T — treatment

One WSL Arch Linux / rootless Podman allocation: 8 synthetic 1024×640 screenshots × four arms = exactly 32 model calls, one per cell. No retry, replacement or candidate rerun. Arms: `FULL_RESOLUTION`, `OVERVIEW_PLUS_CANDIDATE_CROP`, `OVERVIEW_ONLY`, `CANDIDATE_CROP_ONLY`; case-rotated order. Same task meaning and JSON response schema; temperature 0, seed 2031, `num_predict=128`.

Candidate rule: partition each source into four fixed 512×320 tiles; select greatest mean adjacent-pixel grayscale edge difference; ties choose lowest tile index. Rule never reads oracle labels. The eight cases cover duplicate contexts, edge/small target, small text, target absent, target missed by candidate, ambiguity, and icon-adjacent label. Two unique present targets lie outside the selected candidate tile.

Candidate harness image: `docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067` (CPU harness). Inference image: `docker.io/ollama/ollama@sha256:9c1dc45ea758396139ec0adfa52947714c61f8d1e4537a6e2daef8138e7a64a9`. Model: `gemma3:4b`, ID `a2af6cc3eb7f`, weight layer `sha256:aeda25e63ebd698fab8638ffb778e68bed908b960d39d0becc650fa981609d25` (3,338,792,448 bytes). Ollama cloud disabled. Internal Podman network only. Logs detected RTX 3080 Laptop, CUDA compute 8.6; during the formal allocation Ollama reported `100% GPU`, and `nvidia-smi` reported 42% GPU utilization / 3927 MiB used.

## D — decision / audit

Candidate call cap 32. Independent raw auditor cap preregistered as one invocation, only after candidate success. Preserve exact request/response bytes, hashes, model counters and timings. Auditor recomputes canonical payloads, source mapping, crop ranking, and target-box scoring from truth-separated fixtures. Coordinate is correct only inside the unique target box; absent/ambiguous require abstention. Missing/corrupt evidence or any execution deviation is STOP/HOLD, never silently PASS. No aggregate benefit claim at n=8 per arm.

### Observed result

The 32/32 candidate calls completed once. Independent audit reconciled all rows and bytes on the successful run, but the first auditor launch stopped before reading inputs because its destination was on a read-only mount. The output path was corrected and the auditor was invoked a second time. This exceeds the preregistered one-invocation auditor cap; therefore execution protocol is `STOP_DEVIATION`, not a clean protocol PASS. Candidate data were not rerun or altered; both the failed invocation and successful audit output are retained in the task/Issue record.

| Arm | Correct / 8 | Request bytes | Image bytes | prompt_eval_count | eval_count |
|---|---:|---:|---:|---:|---:|
| FULL_RESOLUTION | 1 | 294,146 | 216,976 | 3,268 | 168 |
| OVERVIEW_PLUS_CANDIDATE_CROP | 1 | 426,355 | 315,626 | 5,713 | 168 |
| OVERVIEW_ONLY | 1 | 283,546 | 209,018 | 3,252 | 167 |
| CANDIDATE_CROP_ONLY | 1 | 147,059 | 106,608 | 3,273 | 136 |

Both target-present cases where the crop omitted the target were incorrect in crop-only (2/2). The combined overview+crop arm had the greatest request bytes, image bytes and prompt-evaluation count. Result: `NO_MODEL_UTILITY_DEMONSTRATED_ON_THIS_SYNTHETIC_ALLOCATION`; no attention-representation or runtime promotion.

**Scoring interpretation correction:** candidate selections commonly omit the `abstain` field; the frozen scorer treats a missing field as invalid (`invalid_abstention_type`) and scores it false. Therefore 1/8 per arm is not a valid pure localization-accuracy count. The retained raw records expose coordinates/labels, but this implementation mismatch requires a separately preregistered scoring successor for coordinate-accuracy claims. Do not alter the retained audit or report the 1/8 values as established model accuracy.

## C — caveats

Synthetic fixtures, one model snapshot, one prompt family and one heuristic; not a representative GUI distribution. `prompt_eval_count` is the server prompt metric, not an image-token count. JSON bytes do not measure backend memory or latency. No user data, GUI input, product integration, human-tempo, universal cost, causal benefit or population-rate claim.

## U — open boundary

Real GUI generalization, candidate recall, provenance attacks, product fallback behavior, human tasks, and latency/quality tradeoffs remain open. Prior #1968/#2173 construction evidence remains immutable and separate. This closes only the narrow local allocation, with the explicit auditor protocol deviation.

## Source and evidence inventory

All experiment files are under `research/analysis/model_localization_2031_gemma3gpu_t1_v1/`. `formal/candidate/calls/` contains 32 directories, each with byte-exact `request.json`, `response.json`, and `record.json`; the candidate index and independent audit are retained. `SHA256SUMS` records every retained file except itself. Five non-model construction tests passed before the formal calls. GitHub preregistration and execution note are on Issue #2031. The concise handoff is in [REPORT.md](REPORT.md).
