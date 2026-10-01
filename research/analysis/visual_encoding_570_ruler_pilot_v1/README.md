# Issue #570 — local RAW vs BORDER_RULER pilot

This is a no-authority, synthetic-only visual localization allocation. It uses
the same frozen source screenshots, task prompts, source-coordinate JSON schema,
local vision model and seed in each paired arm. The sole presentation change is
sparse coordinate ticks in blank, renderer-reserved margins.

## Frozen allocation

See `FREEZE.json`. The runner must be invoked at most once. It stops on the
first request failure, does not retry, and refuses to overwrite an existing
`results/formal01/` directory. No OS input, GUI mutation, user data, remote
provider or model update is involved. An absent target requires explicit
abstention.

## Reproduction

Requirements on the recorded host: Python 3.11.9, Pillow 10.4.0, Ollama
0.34.4, and the already-cached `qwen2.5vl:3b` digest recorded in the freeze.
The local Ollama API must be available at `127.0.0.1:11434`.

```powershell
python research/visual_encoding_570_ruler_pilot_v1/run_pilot.py
python research/visual_encoding_570_ruler_pilot_v1/audit_pilot.py
```

The second command is an independent raw-only audit and must run only after the
single runner invocation has terminated. Preserve the first outcome even if it
is incomplete. `FORMAL_RESULT.json`, `RAW.jsonl`, the source and ruler PNGs,
`AUDIT.json`, and their hashes are the retained outputs. The `ollama ps` and
`nvidia-smi` snapshots in the formal result document which local inference
backend was actually used.

## Scope

This does not test fine-tuning, click execution, real-app grounding, task
effects, calibration, product behavior, or general multimodal capability. A
positive screen may justify only a separately frozen held-out confirmation.
