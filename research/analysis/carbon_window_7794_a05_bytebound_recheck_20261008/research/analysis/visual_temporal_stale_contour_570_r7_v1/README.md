# Issue #4763 — stale temporal visual cues on fresh application panels (R7)

This is a fresh successor to #4754's pre-call launcher STOP and #570. R6 made zero model requests and is preserved unchanged. R7 uses fresh seeds and fresh screens; it asks whether previous-frame context helps target localization after a UI update, and whether a red prior-location outline can misdirect a vision-language model. It does not repeat the static ruler/grid/crop ladder in #4738.

## H / T / D / C / U

- **H:** on 10 moved-target and 2 absent-current synthetic panel pairs, paired prior/current frames preserve positive hits and absent abstentions versus the current-only screenshot while reducing current-target center error by at least 0.05 screen diagonals. The stale contour arm tests whether a prior-target outline attracts predictions to a now-different action.
- **T:** 12 fresh independent 1280×800 panel pairs (10 positive + 2 absent), 3 matched views each, exactly 36 one-shot Qwen2.5-VL 3B Q4_K_M requests on the local RTX 3080. Formal seeds are 9320101, 9320204, 9320307, 9320410, 9320513, 9320616, 9320719, 9320822, 9320925, 9321028, 9321131, 9321234; construction seeds are 9320779 and 9320887. Construction uses two disjoint pairs and zero model calls. Formal order is counterbalanced over source cases. Docker has an internal network only, no published ports/egress, a read-only model/source mount, and `--gpus all`. A separate networkless, GPU-less container audits exact raw records. R7 fixes R6's `helper(..., timeout=900)` signature mismatch and exercises launcher tests before inference.
- **D:** `PASS_TEMPORAL_HELP_SCOPED` requires full integrity and GPU evidence, paired-history positive hits and absent abstentions no worse than current-only, and at least 0.05 lower mean normalized target-center error. `FAIL_STALE_CONTOUR_MISDIRECTION` flags ≥2 additional stale-location selections on positives or any false positive on an absent-current case. Otherwise a clean run is `REJECT_NO_TEMPORAL_GAIN`; integrity/provenance/GPU failures are HOLD/STOP. Stale-cue harm is orthogonal to paired-history help, so both labels can coexist.
- **C:** synthetic screen rendering, one model/quantization, one GPU and two negative controls. Paired-history current pane is half-width and is scored through a frozen invertible mapping. Added temporal pixels may help or hurt; no direction is assumed.
- **U:** no live GUI, user data, clicks, training, GPU-versus-CPU causal claim, general latency or safety claim, or runtime authority. Raw current observation remains source of truth. Any pass only motivates a fresh real-frame/effect experiment.

## Frozen conditions

1. `CURRENT_RAW`: exact current 1280×800 pixels.
2. `PAIRED_HISTORY`: previous and current screens side by side with an explicit label strip; right-pane coordinates map by `source_x=2*(shown_x-640)`, `source_y=(shown_y-40)*800/760`.
3. `STALE_CONTOUR`: current pixels with the prior frame's target action region outlined in red. In the current frame, that old row is now a different action or the target is absent.

The target is `Publish` in Project Atlas / Current Actions. A same-label distractor remains in Project Borealis. On absence controls, the old Project Atlas target disappears while the Borealis label remains. Scoring uses IoU≥0.5 for a positive hit, explicit `present=false, box=null` for abstention, old-box IoU≥0.5 for stale-location selection, and predicted-box-center to current-target-center distance normalized by the 1280×800 screen diagonal.

## Execution and evidence

Run `prepare.py` before freezing, then run the independent `audit.py --inputs-only` in the pinned helper. Formal execution is one invocation of `launch.py`; `model_runner.py` refuses model identity mismatch, saves the exact image-bound request and response per call, and performs no retries. `audit.py` independently verifies source/presentation/request hashes, mapping, schedule, response schema and per-call GPU overlap. `sampler.py` records 200 ms GPU-memory/utilization and `ollama ps` samples.

The local Windows Arial font is a read-only input; only its SHA is published. PNG bytes are preserved as `.png.b64` text objects in GitHub because the GitHub contents API accepts text; the manifest hashes decoded PNG bytes.
