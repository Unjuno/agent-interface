# Boundary replay revalidation — 2026-09-27

## Why this successor record exists

After PR #4592 merged, its PASS predicate was audited and found too weak: an equal or ordered case could be counted as PASS even if the guard returned a cancellation receipt or its operands row were absent/mismatched. The raw #4592 output was not overwritten. PR #4593 added exact row/receipt checks and negative controls; both `boundary-pass-gate` and `replay-gate` CI checks passed before that correction merged as `75b3d1e9cf1518ed7912670ea541fe969b2fb0cd`.

This revalidation reruns the same retained real-observation inputs under the corrected main-branch gate. It is a separate additive output path; it is not a new seed allocation or natural-clock reproduction.

## H/T/D/C/U

- **H — Hypothesis:** The corrected gate will accept the three intended capture-relative deltas only when every case has one matching v13 record and the expected production-guard receipt/error, and will reject the false-positive controls already covered by the merged regression tests.
- **T — Test:** Reuse the retained seed-990643 Docker session's typed observations and the same production guard/effective v13 controller; inject capture−1, capture, and capture+1 ns through the main-branch replay harness. Run the harness in the pinned image with no network, read-only root/source, and a separate writable output mount.
- **D — Data:** Current repository main at intake `d6dacd3507ea23a7c5aafe82788c0a9d8b452834`; controller `map01_overlap_controller_v39.py` blob `321ec02e5c3c8bd87c6370e4a5e90bb3013d4241`; guard `running_action_guard_v1.py` blob `d54047e78bc76f53ef47c6f70fd4a3be6318f09c`; v13 adapter blob `45bce226dd6ae8fee044d5516d4b5a5428cc727c`; corrected replay harness blob `6c7faafd028eda44771ba8fde297a51f757da2c0`; effective controller SHA-256 `5ba55ce2007b6214438618ac32ceb9b49b6bc63c522ff7a17912b883b68250d5`.
- **C — Control:** Same two typed observations, contract/action, guard implementation, effective source and output schema as #4592; only the explicitly injected controller-decision timestamp differs. Each case has its own freshly initialized guard. No model invocation or physical key/button action is made.
- **U — Uncertainty:** This establishes the instrumented boundary behavior under controlled timestamps only. The calibration/host/runtime fields are null for injected timestamps. It does not reproduce or explain the natural #4544 clock inversion, validate physical-action safety, or establish gameplay/task success.

## Result and independent audit

Status: `PASS_CONTROLLED_BOUNDARY_REVALIDATION` only.

- Docker harness returned PASS for exactly three cases: −1 ns raised `controller decision precedes current snapshot`; 0 ns and +1 ns returned without exception.
- All three rows independently match summary capture, decision, signed delta, observation sequence and source-event sequence/capture; each guard receipt remains `INPUT_ACTIVE` with logical admission true. The inverted record was flushed before the guard exception.
- The JSONL bytes equal the prior retained `-01` rows; the new `-02` summary adds the observation sequence and was produced by the corrected exact-result gate. This preserves the earlier experiment rather than rewriting its output.
- Current-main `test_diagnostic_capture` passed 5/5 locally; `py_compile` and `git diff --check` passed. PR #4593's two CI checks (`boundary-pass-gate`, `replay-gate`) are green.

## Reproduction

Effective controller generation:

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_policy_invalidation_clock_4559_v1/adapter_v13.py \
  --prepare-only research/doom/map01_overlap_controller_v39_effective_v13.py
```

Pinned Docker invocation (read-only `/src`, network disabled, `/results` writable):

```sh
docker run --rm --platform linux/arm64 --network none --read-only --workdir /tmp \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  -e PYTHONPATH=/src:/src/research/real_apps_v1 \
  -v "$PWD:/src:ro" -v "$PWD/research/doom/map01_policy_invalidation_clock_4559_v1/results:/results" \
  --entrypoint python3 \
  issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e \
  -B /src/research/doom/map01_policy_invalidation_clock_4559_v1/replay_real_observation_boundary_v13.py \
  --events /src/research/doom/map01_policy_invalidation_clock_4559_v1/results/zero-model-preflight-v13-20260927-01-retry04/runtime/events.jsonl \
  --controller /src/research/doom/map01_overlap_controller_v39_effective_v13.py \
  --out /results/real-observation-boundary-v13-20260927-02
```

Image platform/digest: linux/arm64, `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`.

## Retained outputs

Under `results/real-observation-boundary-v13-20260927-02/`:

- `summary.json` SHA-256 `05445612872a796002fe91e68cf447454a74b78a0dfc3a706345da138ca4478e`.
- `inverted.jsonl` SHA-256 `d0cdd76ea8183abe8057fa8a4cdd0b18e7e86dd49166466427ff9a9649f0bc4c`.
- `equal.jsonl` SHA-256 `f8558e148b8acd06ce882f75fe257b0b8bbf8ac6873a6a81d28ac79dd62e67be`.
- `ordered.jsonl` SHA-256 `22f6dd74d8f6f519ed919634dc46659432c9b652eec95d37e010ee72a900c5c2`.

Formal seed `990642` remains a separate, gated allocation; this rerun does not consume it.
