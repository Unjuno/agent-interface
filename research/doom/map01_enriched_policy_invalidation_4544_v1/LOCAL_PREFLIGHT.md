# Local Windows + Docker preflight evidence

Date: 2026-09-27 (Asia/Tokyo)
Scope: zero-model local runtime startup/release only; not a formal allocation.

## Frozen local setup

- Host: Windows Codex desktop, local `codex.exe app-server --stdio`.
- Model configuration: `gpt-5.6-luna`, effort `low`; report has zero planner turns.
- Container: locally built `agent-interface-map01-4544-local:amd64`,
  `linux/amd64`, image ID
  `sha256:d9ceb63e8eb71c82a0094a6d0c44bb6d60a9e7e3f635211fa6f1fc2409511ff7`,
  size 1,140,033,132 bytes (1.14 GB). Not pushed or pulled for runtime.
- Runtime: ViZDoom 1.3.0, MAP01, `ASYNC_SPECTATOR`, ticrate 35, skill 1,
  600-second configured horizon, no fixture, no gameplay input.
- Network disabled inside runtime container; source mounted read-only; no GPU.
- Freedoom 0.13.0 WAD size 28,787,748 bytes; SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Adapter command used an unused local output directory and seed 990644:

  ```text
  python research/doom/map01_enriched_policy_invalidation_4544_v1/adapter.py --out %TEMP%/agent-interface-4544-local-runtime/preflight-zero-model-v4 --iterations 0 --seed 990644 --model gpt-5.6-luna --effort low
  ```

Seed 990644 belongs only to this zero-decision preflight and must not be treated
as or reused for a formal allocation.

## Result

PASS for the bounded runtime-startup/release contract:

- `report.json`: `iterations=0`, `planner_turns=0`, `model_wall_seconds=0.0`.
- Three typed observations reconciled to exact artifact RGB hashes.
- The adapter's observe-only self-test was accepted and completed.
- Terminal owner release was verified with `keys_down=[]` and `buttons_down=[]`.
- Three same-session clock probes; offset uncertainty width 14,626,168 ns.
- Runtime acceptance followed translated observe-only send by 60,633,974 ns.
- The report explicitly withholds evaluator score.

This does not exercise a policy invalidation through the new converter, a model
turn after invalidation, a complete action horizon, any gameplay input, or task
success.

## Retained failures

Each attempt used a distinct output path; no formal run was started:

1. `preflight-zero-model-v1`: inherited controller attempted the unavailable
   macOS Codex path and stopped before session/game startup.
2. `preflight-zero-model-v2`: Windows Codex started, but inherited per-MCP
   configuration failed with `invalid transport` during app-server initialize.
3. `preflight-zero-model-v3`: app-server initialized; runtime import stopped on
   missing `openpyxl` before the MAP01 session began.
4. `preflight-zero-model-v4`: passed the scoped startup/release checks above.

Fixes: point the shared app-server executable at the installed Windows Codex
binary; use a valid empty MCP configuration; pin `openpyxl==3.1.5` in the local
image. No production decision gate was relaxed. The first two failures created
only an empty planner-protocol journal; the third stopped before session
startup. The separate output directories and their logs remain in `%TEMP%`.

## Hashes / raw evidence location

Raw preflight output is committed beside this record at
`artifacts/preflight-zero-model-v1/` through
`artifacts/preflight-zero-model-v4/`; the original host copies remain at:

```text
C:\Users\junny\AppData\Local\Temp\agent-interface-4544-local-runtime\preflight-zero-model-v4
```

Key SHA-256 values:

- Dockerfile: `44f813c69c9dd65e4cf849d6730fcfe8de7939b8944cb01d4c8345ecf3b5c827`
- Adapter: `9f457ac4f6663f09a775e3852b4c157c9dc8c69b04b7e7ea583b966f4dbb04a8`
- Receipt translator: `21f8d91f369d8ef55b5db5e8ce7b7bcc13a9418f6dd7c1ea02e6b340f07370d4`
- Test file: `023b118a1a86b249762cd832766fe8c5214cf4d40a7876dc3f781fd8fcaa5460`
- Generated effective controller: `8ee8de8ffae4074fa11cd360aac8ca42325473e2cf8fa424b84ebfc7d1d6c117`
- `report.json`: `3220aabfcd70e937ad166c4bbf982ab412d3bf1a7869c7a7f2bef44f4e4ebedd`
- `runtime/submit-clock-zero-decision.json`: `bc6e57339b212f78498dbe49112ad6bbd37390b9b36393f832296902d49bbc89`
- `runtime/events.jsonl` and `runtime/delivered.jsonl` (identical):
  `02fabc72d637e8c17e81d899bc7d8f17383836d6da70b4c8674749cfff3109e3`
- `runtime/environment.json`:
  `381da276cc09d4330af272fe3ead8f45f106b00d66da650a2d7274d5c9fe153f`
- `planner-protocol.jsonl`:
  `95f41aa03f835cf8939e11157b2eb2d6bca70621330dea70348e8537f2ffce33`

Independent replay audit:

```text
python -B research/doom/map01_enriched_policy_invalidation_4544_v1/audit_local_preflight.py
PASS_LOCAL_ZERO_MODEL_STARTUP_RELEASE_AUDIT
planner_turns=0 typed_observations=3 verified_empty_owner_releases=3
clock_uncertainty_ns=14626168
runtime_source_hashes=20/20
```

`runtime/sources.json` binds all 20 runtime files to their exact repository
contents; all hashes were independently checked against current `main` after
updating the checkout. Per-file raw artifact hashes are in `SHA256SUMS.txt`.
The complete result and bounded interpretation are also recorded in Issue
[#4544](https://github.com/Unjuno/agent-interface/issues/4544). The image is
kept local; the hashes make this particular build identifiable but do not
claim it is a portable published image.
