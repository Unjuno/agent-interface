# Offline R93 Calc plan replay through Fake X and public MCP

## Question
Can the saved structured R93 plan be translated into the registered Calc task values, then carried through fresh observation, stale-observation refusal, bounded retry, input release, and an independent task-effect check without another model/provider call?

## Source and conditions
- Historical source: `source-r93/worker-result.json` and `source-r93/published-request.json`, copied byte-for-byte from the retained R93 packet.
- Historical model usage: 11,938 input tokens, 76 output tokens, 12,014 total; this is prior usage and is not charged to either replay.
- Adapter: strict fixed-task translation in `runtime/guarded_x11_v1/calc_model_plan_adapter_v1.py`. It accepts only the expected Sheet1/A1/blank/action sequence, a finite confidence at least 0.90, and exact fields. Confidence is a rejection-only check, not proof of correctness.
- Authority: the translated answer carries no coordinates, window/session identity, aliases, or permission. Each run obtains fresh observation and current server-minted aliases through the existing public MCP caller and guarded Calc path.
- Environment: local Windows Python, FakePlanner, Fake X Calc fixture, public MCP caller; no live model/provider and no live Calc desktop target.
- A prior-observation change is injected while the first synthetic provider generation is held. That generation is refused without Fake X input. One fresh observation/generation then proceeds through the bounded Calc profile.
- Four retained runs across two confirmations: normal Python and optimized (`python -O`), each repeated once as `windows-run-02` and `windows-opt-run-02`.

## Commands
Run from `research/integration/standard_mcp_task_ledger_57_v1` with repository root on `PYTHONPATH`:

```powershell
$env:PYTHONPATH='D:\ai57-main-current-20261104'
$env:AGENT_INTERFACE_RETAIN_CALC_PROVIDER_WAIT_EVIDENCE='D:\ai57-main-current-20261104\research\integration\standard_mcp_task_ledger_57_v1\calc-model-plan-replay-20261104-01\windows-run-01'
python -m unittest -k calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases test_mcp_endpoint_composition.py

$env:AGENT_INTERFACE_RETAIN_CALC_PROVIDER_WAIT_EVIDENCE='D:\ai57-main-current-20261104\research\integration\standard_mcp_task_ledger_57_v1\calc-model-plan-replay-20261104-01\windows-opt-run-01'
python -O -m unittest -k calc_provider_wait_stale_refusal_then_one_fresh_attempt_releases test_mcp_endpoint_composition.py
```

The test uses synthetic provider accounting and waits. It is not a matched latency/cost benchmark.

## Results
All four retained runs passed (one test each). Each `boundary-results.json` records:
- replay source SHA-256 `24a3b0abf462f3de5a9ab71d593095048abab8bd3ff236057dfce75284d7e04a`;
- adapted task values A1=`731`, A2=`864`, with no new provider call;
- stale first attempt refused before input, then one fresh attempt completed the registered two-transition Calc route;
- all transition input releases verified, followed by owner close with release confirmation;
- final state independently verified after close, and the saved FODS cell values matched `731` and `864`.

The method receipt correctly remains `SAFE_YIELD` with `effect_unavailable` at its save handoff. The separate post-close verifier reports task success. This is a Fake X integration result only; it does not establish live Calc/MAP01 behavior or efficiency improvement.

## Integrity
`sha256-manifest.txt` covers this README, both raw R93 source files, both run packets, and all retained raw files, excluding the manifest itself.

## Implementation source hashes
- `runtime/guarded_x11_v1/calc_model_plan_adapter_v1.py`: `409870b3dd03c65f48c4902cc0145690cbefa6a333bdc6b048825b13f78d1fbe`
- `runtime/guarded_x11_v1/test_calc_model_plan_adapter_v1.py`: `99c9331331529b9d635cc97b62294381cda01bd3442b4f8e2ea66e8151563783`
- `research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py`: `f78fb733f866aa725a277d30b9b492984d341673aba9846421b7c31560436e24`

