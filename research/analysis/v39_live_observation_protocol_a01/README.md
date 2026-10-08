# V39 live-observation App Server protocol probe (A01)

## Question

Can a fresh external observation be attached to an already-running Codex App Server turn, and can its retained PNG be verified in the next model request?

## Result

On Codex CLI 0.160.0, a loopback-only mock Responses endpoint received the V39 sequence-200 observation during an active App Server turn. The initial and ExternalMessage `turn/start` replies contain the same nonempty turn ID. With image detail `auto`, the second mocked request contains both the observation text and the exact PNG bytes. With `detail=low`, the text arrives but the CLI omits the image. The saved outcomes are `results/a01-auto.json` and `results/a01-low-control.json`; the latter is an expected negative control and the probe exits 1 because its required image is absent.

The PNG is from `map01-v39-coast-liveness-live-01/runtime/200.png`, sequence 200, from the retained allocation at commit `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`. Its PNG SHA-256 is `0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`.

## Reproduction

From the repository root, provide a checked-out copy of the retained PNG (the sparse checkout may not materialize it):

```powershell
python research\analysis\v39_live_observation_protocol_a01\probe.py --frame C:\path\to\v39-seq200.png --detail auto > research\analysis\v39_live_observation_protocol_a01\results\a01-auto.json
python research\analysis\v39_live_observation_protocol_a01\probe.py --frame C:\path\to\v39-seq200.png --detail low > research\analysis\v39_live_observation_protocol_a01\results\a01-low-control.json
python research\analysis\v39_live_observation_protocol_a01\audit_result.py
python -m unittest research.analysis.v39_live_observation_protocol_a01.test_probe -v
```

The probe verifies the PNG hash before starting. It launches `codex app-server` with a temporary `CODEX_HOME`, points the configured provider at a server bound to `127.0.0.1`, removes `OPENAI_API_KEY` from the child environment, and checks that the two RPC replies carry the same turn ID. It also asserts text/image delivery, completion, and absence of mock-server errors. No real model endpoint or API key is used. The `low` probe's exit 1 is expected; it retains the text-only negative result.

The independent raw-result auditor checks both response IDs rather than trusting the candidate's same-turn flag, the pinned image hash, request count, text and image outcomes, loopback markers, and server errors.

## H / T / D / C / U

- **H:** App Server ExternalMessage can carry a fresh observation into the active turn's next model request, including the retained image, when sent with a supported image detail setting.
- **T:** Hold the first mock response pending; send ExternalMessage on the same thread; capture the follow-up request; compare reply turn IDs and exact text/image payloads for `auto` and `low`.
- **D:** `auto` passes only if same-turn IDs match and both text and the one exact image arrive. The `low` control is expected to preserve text and omit the image.
- **C:** This establishes transport behavior only; a real model may ignore or misinterpret the image or may not reconsider its in-flight plan.
- **U:** No real inference, visual comprehension, feedback effect, control cancellation/release, V39 runtime invocation, GUI/game, or live threat measurement was tested. This does not satisfy Issue #59's fresh-current-main live threat gate. The private lane remains unassigned.

## Sources

- [Codex Python SDK FAQ: ExternalMessage and active-turn behavior](https://github.com/openai/codex/blob/main/sdk/python/docs/faq.md)
- [Codex Python SDK API](https://github.com/openai/codex/blob/main/sdk/python/src/openai_codex/api.py)
- [Issue #59](https://github.com/Unjuno/agent-interface/issues/59)

