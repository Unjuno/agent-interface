# #4563 experiment record — 2026-09-27

## Result

Two scoped gates passed in the pinned Linux/arm64 Docker runtime. This is not a formal model run and does not reproduce a naturally occurring clock inversion.

1. The allocated zero-model MAP01 preflight seed `990643` started Freedoom 2 MAP01/skill 1, emitted three typed observations, reconciled all three against exact image artifacts, and shut down with three independently verified empty owner releases. It used no model decisions (`iterations=0`, `model_wall_seconds=0`). No fixed threat fixture was loaded; `runtime_fixture` is null.
2. A controlled boundary replay used the real typed observations captured by that Docker session and the production `RunningActionGuard` plus v13 `DoomRunningActionMonitor`. With the same action/contract and observation-bound fields, injected decision deltas of -1 ns, 0 ns, and +1 ns yielded respectively: the original `ValueError` after the v13 JSONL row was written; accepted check with no exception; accepted check with no exception. No physical input was sent. The inverted case leaves the guard's logical mock admission active; it is not evidence of active physical input or safe release.

The useful result is narrow: for an authentic same-session typed observation, v13 records its exact sequence/capture timestamp and the explicitly supplied decision timestamp *before* the guard's timestamp-order validation raises. Calibration/host-clock fields are null here because the harness deliberately injects the timestamp; this test does not diagnose the source of #4544's original inversion.

## H/T/D/C/U

- **H — Hypothesis:** Capturing operands at the guard boundary will preserve enough exact evidence to distinguish decision-before-capture from equality or normal ordering when the clock inversion is encountered.
- **T — Test:** Run the v13 adapter with zero model iterations in the pinned Docker image; then replay two later typed observations through the real guard/monitor with only `controller_decided_ns` varied to capture−1, capture, and capture+1.
- **D — Data:** Seed 990643; MAP01 skill 1; typed sequences 1–3; two exact observation payloads for sequences 2 and 3; artifact reconciliations 3/3; verified empty owner releases 3/3; boundary deltas −1/0/+1 ns. Source/effective controller SHA-256: `5ba55ce2007b6214438618ac32ceb9b49b6bc63c522ff7a17912b883b68250d5`.
- **C — Control:** Same pinned image, captured observations, action, validity contract, production guard and v13 monitor. Only the injected controller decision timestamp changes. The harness disables model calls and never submits a key/button action.
- **U — Uncertainty:** Artificial timestamp injection; no original #4544 operands recovered; no clock-domain diagnosis; no model or fixed threat fixture; no gameplay/task-effect claim; no physical-action safety claim. The full 24-decision formal seed 990642 remains unstarted pending final worker ownership/collision confirmation.

## Reproduction

Pinned image: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e` (linux/arm64). WAD SHA-256: `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

Preflight command:

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_policy_invalidation_clock_4559_v1/adapter_v13.py \
  --out research/doom/map01_policy_invalidation_clock_4559_v1/results/zero-model-preflight-v13-20260927-01-retry04 \
  --iterations 0 --seed 990643 --session-span 4 --model gpt-5.6-luna --effort low
```

Boundary replay command (run inside the pinned image with `/src` read-only and the experiment `results/` directory mounted read-write):

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -B research/doom/map01_policy_invalidation_clock_4559_v1/adapter_v13.py \
  --prepare-only research/doom/map01_overlap_controller_v39_effective_v13.py

python3 -B research/doom/map01_policy_invalidation_clock_4559_v1/replay_real_observation_boundary_v13.py \
  --events research/doom/map01_policy_invalidation_clock_4559_v1/results/zero-model-preflight-v13-20260927-01-retry04/runtime/events.jsonl \
  --controller research/doom/map01_overlap_controller_v39_effective_v13.py \
  --out research/doom/map01_policy_invalidation_clock_4559_v1/results/real-observation-boundary-v13-20260927-01
```

## Retained output and audits

- Preflight: `results/zero-model-preflight-v13-20260927-01-retry04/`; `report.json` SHA-256 `360567159b752980d0c2b8c1b931f99876efdacbb373375c973e301bb103b3be`; `runtime/owner-events.json` SHA-256 `e7b623459820d1c6eb71073d08e725959d8949898484c3f6646ee20d695aadce`; `runtime/events.jsonl` SHA-256 `a040a342471df48580c1207ac88c25d711c2753ecdb9ef71417ec4cb6627d1e7`; `runtime/environment.json` SHA-256 `72072edf1a1ee3e72b21511019a5992918e86cc8882d189ffce07afdbab7a0b9`.
- Boundary: `results/real-observation-boundary-v13-20260927-01/summary.json` reports PASS; JSONL hashes: inverted `d0cdd76ea8183abe8057fa8a4cdd0b18e7e86dd49166466427ff9a9649f0bc4c`, equal `f8558e148b8acd06ce882f75fe257b0b8bbf8ac6873a6a81d28ac79dd62e67be`, ordered `22f6dd74d8f6f519ed919634dc46659432c9b652eec95d37e010ee72a900c5c2`.
- Container source manifest: `runtime/sources.json`; WAD identity is also recorded in `runtime/environment.json`.
- Failures retained in the experiment workspace: initial launch failed because the sparse checkout lacked `map01_motor_responder_v10.txt` and `map01_cover_policy_schema_v6.json`; three subsequent Docker starts exposed missing imports in sequence: `session_v8.py`, `session_v6.py`, then `input_owner_v5.py`. After materializing the exact current-main dependencies in the temporary checkout, retry04 passed. These are checkout setup failures, not semantic test failures. Their raw app-server protocol captures are kept local but not published because they include host and installation identifiers; the exact missing imports and failure classification are retained here. An earlier attempt's already-created output directory was intentionally left untouched.

## Local verification

- `python3 -B -m unittest research.doom.map01_policy_invalidation_clock_4559_v1.test_diagnostic_capture -v`: PASS, 2/2.
- `python3 -B -m py_compile .../adapter_v13.py .../replay_real_observation_boundary_v13.py`: PASS.
- `git diff --check`: PASS.
- Docker boundary replay: PASS, three expected cases; Docker exited cleanly and no container remained.

No guard semantics were changed. The next formal gate remains blocked on documenting final concurrent seed/path ownership and refreshing exact source provenance in Issue #4563.
