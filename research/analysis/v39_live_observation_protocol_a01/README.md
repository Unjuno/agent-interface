# V39 live-observation App Server protocol probe (A01)

## Question

Can a fresh external observation be attached to an already-running Codex App Server turn, and can its retained PNG be verified in the next model request?

## Offline result

On Codex CLI 0.160.0, an App Server `turn/start` carrying an `ExternalMessage` (`input: []` plus `toolOutput`) was accepted on the active thread and returned the same in-progress turn ID. A loopback-only mock Responses endpoint then received a second request containing the observation text and the exact PNG bytes supplied to the external message. The archived frame used here is V39 event sequence 200 from `map01-v39-coast-liveness-live-01/runtime/200.png` at commit `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`; its PNG SHA-256 is `0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`.

The detail setting matters: `low` delivered the text but the CLI omitted the image from the model request; `auto` delivered both. This is an observed transport behavior for this CLI and mock protocol path.

## Run

From the repository root, provide the retained PNG. The worktree sparse checkout does not materialize the raw run, so a checked-out copy is required:

```powershell
python research\analysis\v39_live_observation_protocol_a01\probe.py --frame C:\path\to\v39-seq200.png --detail auto
python -m unittest research.analysis.v39_live_observation_protocol_a01.test_probe -v
```

The runner verifies the PNG hash before starting. It launches `codex app-server` with a temporary `CODEX_HOME`, points the only configured model provider at a server bound to `127.0.0.1`, removes `OPENAI_API_KEY` from the child environment, and returns a nonzero exit if the same-turn, text, image, completion, or server-error checks fail. Its JSON report avoids printing image data.

## Hypothesis / disposition

**H:** App Server ExternalMessage can carry a current observation into the active turn’s next model request, including its retained image, when sent with a supported image detail setting.

**D:** Supported at the local protocol/transport boundary in this isolated mock test. `detail=low` failed image delivery; `detail=auto` passed.

## Limits and next test

The endpoint is a mock and performs no inference. The test does not establish that a real model notices or correctly interprets the observation, that feedback changes an uncommitted plan, that the GUI/game actor releases or cancels existing work, or that the V39 controller can invoke App Server ExternalMessage. It does not alter the live allocation status or satisfy Issue #59's fresh-current-main live threat gate. The next test needs the assigned live lane and should measure whether the observation can stop or switch an inappropriate in-flight cover action before model return, with exact capture, message, cancellation/release, and action timestamps.

## Sources

- [Codex Python SDK FAQ: ExternalMessage and active-turn behavior](https://github.com/openai/codex/blob/main/sdk/python/docs/faq.md)
- [Codex Python SDK API](https://github.com/openai/codex/blob/main/sdk/python/src/openai_codex/api.py)
- [Issue #59: current allocation and live-control priority](https://github.com/Unjuno/agent-interface/issues/59)
