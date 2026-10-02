# Issue #3850 — model-facing diagnostic repair pilot

Disposition before execution: preregistration only; formal calls = 0.

## H — hypothesis

For two previously observed malformed `observe` programs, a bounded diagnostic (`detail`, `detail_source=program_validation`, and `validation_operation_index`) will let the same model produce more exact, scope-preserving static repairs than the generic `INVALID_PROGRAM` code alone. This is a small model-facing recovery signal, not task completion or a product claim.

## T — frozen comparison

- Current-main intake: `f34b5b43446f6a276fedfc2cd587e823d69264b1`.
- Diagnostic source blob: `runtime/cli_v1/api.py`, Git blob `6318f0d2fe0b0533d694175e2521eb86946dbed1`.
- Review source blob: `runtime/cli_v1/review.py`, Git blob `0b9294a6f587ea4dc1d2a40187509628af7336fc`.
- Documentation blob: `runtime/cli_v1/README.md`, Git blob `144bee995bfb760b49fffbbdac7a6c0e65b0fe49`.
- Two fixed cases, two repetitions, two conditions = eight one-turn calls. Each case uses a frozen malformed program with one `observe` and a `release_all`; no dispatch or input is permitted.
- Exact case 1 input (`region` form): `{"schema":"agent-interface/program-v1","program_id":"diag-region","source":{"observation_seq":1,"binding_revision":1},"authority":{"lease_id":"fixture-not-authority","expires_at_ns":9999999999999},"terminal":{"release_all_required":true},"ops":[{"op":"observe","frame":"window_client","region":{"x":10,"y":20,"width":300,"height":200}},{"op":"release_all"}]}`. Expected repair changes only the `observe` object to `{"op":"observe","frame":"window_client","x":10,"y":20,"w":300,"h":200}`.
- Exact case 2 input (`width`/`height` form): `{"schema":"agent-interface/program-v1","program_id":"diag-width-height","source":{"observation_seq":1,"binding_revision":1},"authority":{"lease_id":"fixture-not-authority","expires_at_ns":9999999999999},"terminal":{"release_all_required":true},"ops":[{"op":"observe","frame":"window_client","x":10,"y":20,"width":300,"height":200},{"op":"release_all"}]}`. Expected repair changes only the `observe` object to `{"op":"observe","frame":"window_client","x":10,"y":20,"w":300,"h":200}`.
- Prompt template: “Continue this action-free request after the listed program was refused before execution. Task: take one read-only observation of frame `window_client` over the ROI x=10, y=20, width=300, height=200. Preserve the ROI and all unrelated program fields. Use the refusal payload below to repair only the malformed field names/shape. Return `READY` only with the complete corrected program; if the valid correction is uncertain, return `YIELD` and the original program unchanged. Do not claim that the program ran or that the task succeeded; do not add task input.” The fixed output schema requires exactly `status` (`READY` or `YIELD`), `program` (object), and `reason` (string); no other keys.
- `CODE_ONLY`: return only `status=refused,error=INVALID_PROGRAM`.
- `BOUNDED_DETAIL`: the same refusal plus exact actual-main detail and source operation index. Case 1: `observe x must be int`, index 0; case 2: `observe w must be int`, index 0.
- Exact result payloads: `CODE_ONLY` is `{"status":"refused","error":"INVALID_PROGRAM"}`. Case 1 detail payload is `{"status":"refused","error":"INVALID_PROGRAM","detail":"observe x must be int","detail_source":"program_validation","validation_operation_index":0}`. Case 2 detail payload is the same shape with `detail":"observe w must be int"`.
- Exact output schema: `{"type":"object","required":["status","program","reason"],"additionalProperties":false,"properties":{"status":{"type":"string","enum":["READY","YIELD"]},"program":{"type":"object"},"reason":{"type":"string"}}}`.
- Each prompt gets the identical task, malformed program, and output schema within its matched pair. The sole changed text is the refusal payload. The prompt asks for a repaired program that preserves frame, ROI, all other fields, and action-free scope; if uncertain, return `YIELD` with the original program unchanged.
- Order: region case rep1 CODE_ONLY→DETAIL; region rep2 DETAIL→CODE_ONLY; width/height case rep1 DETAIL→CODE_ONLY; width/height case rep2 CODE_ONLY→DETAIL.
- Same host Codex CLI `0.158.0-alpha.2`, executable SHA-256 `0122378C15DC0C3C0AF0D6ADDF2DD278125C19676B41FADAA520F89D2C9E0079`; requested model `gpt-5.6-luna`, reasoning `low`; eight fresh one-turn invocations, no retries. CLI wall time and reported token usage are descriptive, not causal latency/cost estimates.
- Each runner is a local Docker Desktop `desktop-linux`, linux/amd64 container using image ID `sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41`; `--network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt no-new-privileges --cap-drop=ALL`. Only the IPC and per-row result mounts are writable. A local host broker forwards one frozen prompt to the host CLI. No GitHub Actions/workflow runs the experiment.
- Formal execution may begin only after the currently active unrelated Docker container `mitra-rung0-853-formal-01` is terminal. It will not be inspected internally, stopped, or modified. Recheck Docker concurrency before each row.

## D — decision gates

- Row integrity: exactly eight distinct request IDs, one completed assistant message and one usage-bearing completed turn per row, broker/runner exits 0, no retries, valid output JSON, and matching request/broker/response identities.
- Exact repair: `READY` counts only when the emitted program equals the independently authored expected repair byte-semantically after JSON parsing, preserves all unrelated fields/ROI/frame, removes malformed fields, and keeps `release_all`; `YIELD` is safe abstention but not successful repair. Any other `READY` is a false repair.
- `PASS_REPAIR_SIGNAL_SCOPED` only if BOUNDED_DETAIL yields more exact repairs than CODE_ONLY across the four matched pairs and has zero false repairs.
- `HOLD_NO_DISCRIMINATING_SIGNAL` for ties, mixed results, or no exact repairs; `FAIL_DETAIL_HARM` if BOUNDED_DETAIL has fewer exact repairs or any detail-arm false repair. Missing/incomplete/provenance failures are `STOP`/`HOLD`, never model failure. No retries or substitutions.
- A complete four-pair result is underpowered and descriptive; it cannot justify a default change or claim saved calls, latency, tokens, task success, or integration-spine completion.

## C — controls

Same model/build/config, host, prompt template, exact malformed inputs, ROI/frame values, JSON response schema, sandbox, one-turn budget, and matched-pair order. Fresh call per row; no conversation carryover, schema/API docs, GUI, image, app, action, external data, local model, or automatic repair loop. The diagnostic is the only treatment. Raw turn events, usage, response bytes, timings, broker receipts, CLI argv/version, container/process exits, source/image identities, and independent audit are retained.

## U — limits

Two authored error shapes, four matched pairs, one task family, no native dispatch or app effect, and no blinded primary-assistant interaction. It tests one-turn repairability under minimal schema context; it does not establish natural error rates, user comprehension, fewer actual recovery calls, token/cost savings, wall-clock benefit, cross-model transfer, or safety of executing a repaired program.

## Planned artifacts and execution boundary

Local output: `results/formal01/`, one directory per row, plus frozen case/prompt JSON and independent audit output. Preserve every first outcome. Record the completed outcome in Issue #3850. Publish the complete additive source/raw evidence by reviewable PR only after the local raw-only audit and applicable local checks pass. No runtime source changes.
