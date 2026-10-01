# Issue #3896 — source-only import-boundary successor

## Outcome: `STOP_SETUP`

No AST audit or formal container invocation was performed. The required Docker Desktop `linux/amd64` environment was unavailable, so the Obstac stop condition was reached before source execution or audit construction. This is an infrastructure STOP, not a classifier result and not evidence that the historical launcher is safe or unsafe.

## Frozen read-only context

- Repository: `Unjuno/agent-interface`
- `main` observed and fetched: `f08fdd934912884c353797615fe8e053e739fef8`
- Issue: [#3896](https://github.com/Unjuno/agent-interface/issues/3896)
- Target `research/doom/map01_r4_sparse_checkout_successor_2174/import_gate.py` blob: `43f3737879f8283220e87871cdae30335605a145` (1272 bytes)
- Target `research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py` blob: `aad69e7dc70d6e072d74619d2be6239eed22ac15` (1505 bytes)
- Required image reference: `python:3.12-slim`, immutable ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, required platform `linux/amd64`.

## Environment evidence

Read-only Docker context inspection found only `default` (`unix:///var/run/docker.sock`) and `orbstack` (`unix:///Users/taka/.orbstack/run/docker.sock`). Both resolve to the OrbStack daemon (`name=orbstack`, server `29.4.0`, architecture `aarch64`). The required cached image is present only as `linux/arm64` under the inspected default context. No Docker Desktop `linux/amd64` daemon/image was available. No image was pulled, no alternate platform was substituted, and no container was started.

## Scope and preservation

The historical #3857 STOP, #3859 workflow-dispatch safeguard, and #2174 launcher were not modified. No historical launcher, dependency, workflow, game, model, or input was imported or executed. No AST classifier/control suite was authored or run. No formal evidence hashes or PASS/FAIL classifier result are claimed.

## Resume condition

Resume only when the exact required Docker Desktop `linux/amd64` image is already cached and available without pulling. Then freeze current source and verifier hashes before one isolated invocation, following the full H/T/D/C/U and stop rules in #3896. If that prerequisite remains unavailable, preserve this STOP and do not retry under OrbStack or another architecture.
