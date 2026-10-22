# V39 external observation compatibility probe: Codex CLI 0.146.1

## Question and result

Does the `turn/start` + `toolOutput` observation shape used by the V39 active-turn composition remain attached to the original in-flight turn on the locally installed Codex CLI 0.146.1, and does the loopback Responses request receive the observation text and frame?

No. Both timing conditions accepted the RPC, but the reply carried a different turn ID. When sent while the initial mocked Responses request was held open, only that initial request was observed; the initial turn completed after release, while the external turn remained incomplete through the 20-second observation window. When sent after the initial turn completed, a second independent turn and request completed, but the exact health/ammo observation and PNG were absent from the Responses input.

This is a client-version compatibility result for the `turn/start` + `toolOutput` shape. It complements the Codex CLI 0.160.0 transport result in PR #7951 and request-ordering result in PR #7969; it does not invalidate those newer-version results. The local CLI version is not evidence that the deployed V39 runtime uses this binary.

## Fixed inputs and isolation

- Experiment checkout base: `402c7d1b5147b2a905098f082233db60a47d68db`, which was `origin/main` when the probe was run. The source probe was copied from PR #7951 head `046d7e2199261b3f58944be75ffef1eabe2220bd` (`research/analysis/v39_live_observation_protocol_a01/probe.py`, SHA-256 `3397a0933444790053a51e1f4ada777c015a15688277a677808c55dfec18beef`) and adapted only to run both timing conditions, retain mock request bodies, and remove the temporary home after exit. While preparing this review artifact, `origin/main` advanced to `6860b585305e539ec93896f5adcbf658cbbd8592`; those commits do not touch this protocol path or the retained fixture.
- Retained fixture: V39 sequence 200 PNG at `research/doom/results/map01-v39-coast-liveness-live-01/runtime/200.png`; SHA-256 `0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`.
- The App Server subprocess received a minimal environment with temporary `HOME`, `CODEX_HOME`, and `TMPDIR`; its only configured model provider was an HTTP server bound to `127.0.0.1`. No API key, remote model, game, GUI, or input backend was used. Each run was bounded to a 20-second external-turn observation window.
- The JSON files under `raw/` preserve actual mock Responses request bodies, the App Server reply fields, runner summaries, and the independent audit output. The retained PNG remains referenced by its path/hash rather than duplicated.

Recorded intervals were 2026-10-05 04:18:24.839228–04:18:47.360709 UTC (22.521 s, during-turn) and 04:18:47.962366–04:19:08.369542 UTC (20.407 s, after-turn). In the first case the external-message reply arrived 2.711 ms after send; the initial Responses request then remained held for 2.005 s before release. Only one model request arrived and the external turn did not complete. In the after-turn case, the second request and external turn completed.

## H / T / D / C / U

- **H:** On CLI 0.146.1, sending the V39 `toolOutput` observation with `turn/start` either during or after an initial turn does not deliver that observation to the model request as an active-turn update.
- **T:** Hold the initial loopback Responses response open and send the external message during that turn; in a second bounded run, finish the initial turn first. Save raw mocked requests and compare both returned turn IDs, turn completions, observation text, and exact PNG data URL.
- **D:** Compatibility fails if the observation is absent, the turn ID changes, or the external turn does not complete in the in-flight case. The independent audit separately verifies the observed request count, raw-body hashes, fixture hash, timing precondition, and completion shape.
- **C:** CLI 0.146.1 is older than the CLI 0.160.0 results in #7951 and #7969. This may be an introduced-version boundary. The probe says nothing about a different method or client build.
- **U:** Loopback protocol only; no real inference, model comprehension, runtime integration on the target host, cancellation/release behavior, independently useful feedback, recovery, task effect, live threat exposure, or MAP01 outcome was tested. Do not claim this closes any Issue #59 gate.

## Reproduction and audit

From the repository root, with Codex CLI 0.146.1 available:

```sh
python3 research/doom/v39_external_observation_cli0146_a01/probe.py \
  --frame research/doom/results/map01-v39-coast-liveness-live-01/runtime/200.png \
  --timing during-turn > research/doom/v39_external_observation_cli0146_a01/raw/during-turn.json
python3 research/doom/v39_external_observation_cli0146_a01/probe.py \
  --frame research/doom/results/map01-v39-coast-liveness-live-01/runtime/200.png \
  --timing after-turn > research/doom/v39_external_observation_cli0146_a01/raw/after-turn.json
python3 research/doom/v39_external_observation_cli0146_a01/audit.py
```

The probe intentionally exits 1 because its positive-delivery assertion is unmet. That exit is the measured negative result; the independent auditor exits 0 when the raw evidence matches the expected negative compatibility outcome.

`raw/audit.json` passed all 30 case-level checks across the two runs, including recomputation of request-body hashes, monotonic send/ack/release ordering, and matching request-type summaries against the preserved raw bodies.
