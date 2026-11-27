# Standard MCP compiled-caller construction check — Fake X

Status: finite synthetic integration evidence only. This was **not** a WSLc
allocation, live GUI run, MAP01 run, independent task score, or efficiency
comparison. No real desktop/application input was sent. It does not satisfy
Issues #17 or #57.

## Question and fixed conditions

Can the public standard MCP route reach the existing bounded compiled graph
through one generation-bound owned X11 caller, refuse continuation after target
generation changes, and retain a conservative result when cancellation meets
blocked platform I/O?

The tests use the repository Fake X backend, a 32×32 synthetic image, one
`CTRL+a` key chord, one exact red RGB transition, finite pixel predicate tables,
and a one-transition graph. The fixture is defined in
[`test_mcp_owned_process.py`](../../../runtime/cli_v1/test_mcp_owned_process.py).
The public tool is enabled only for guarded-X11 startup with process identity,
query worker, and owned process enabled. No callback code is accepted from the
tool caller.

Each of the three scenarios ran once with normal Python and once under `python
-O`. Exact test stdout/stderr is retained in `run-01-normal.txt` and
`run-01-optimized.txt`; each scenario's complete temporary MCP call directory,
including request/report JSON, graph receipts, images and synthetic markers,
is copied under the matching `run-01-*` directory. `SHA256SUMS` covers all
retained files except itself.

## Results

| Scenario | Normal / optimized | Observed result | Limit |
|---|---|---|---|
| Standard compiled route | PASS / PASS | MCP call retained `TASK_SUCCEEDED`, one completed graph transition, and `task_success: null`; result lookup returned the same method receipt. | A successful synthetic method verdict only; no independently scored application task. |
| Generation change after synthetic key press | PASS / PASS | Target generation changed from fixture A to B; graph returned `SAFE_YIELD`, with zero completed transitions and `task_success: null`. | Fake process-identity source and synthetic pixels only. |
| Cancel during blocked platform sync with CTRL held | PASS / PASS | The exact owned process was retired. Input obligation recorded CTRL; cancellation and terminal reports retained `release_confirmed: false`, `cleanup_status: UNKNOWN`, and `replay_allowed: false`. | Disconnect supervision and retired-input release were deliberately mocked; no real XRes disconnect or independent key-up readback occurred. Late server work remains possible. |

The cancellation case blocked in fake `sync()` after CTRL down. The test uses a
short bounded wait for the MCP call to become terminal after owner retirement.
The resulting `runtime_failed` receipt and `cleanup_failed` close receipt are
preserved as uncertainty, not treated as successful release.

The post-merge `native-mcp` failure from this packet's PR and the narrow
`FakeBridge.scope` compatibility correction are recorded with the downloaded CI
logs under [`ci-native-failure`](ci-native-failure/README.md). The compiled
route's original Fake X evidence is retained separately from that regression.

## Reproduction

From the repository root, with the test dependencies installed:

```powershell
$env:AGENT_INTERFACE_FAKE_X_EVIDENCE = "research/integration/standard_mcp_compiled_fake_x11_20261020/run-02-normal"
python -m unittest `
  runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_standard_compiled_profile_uses_generation_bound_owned_caller `
  runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_compiled_profile_stops_mid_action_on_process_generation_change `
  runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_compiled_call_cancel_retires_owner_during_blocked_platform_sync
```

Use a fresh evidence directory for each run; the tests refuse to overwrite
scenario folders. Repeat with `python -O -m unittest` for optimized mode. This
record's source was developed from main `e4246c87e5f3e6f63acb7f424ee7f557f2bfb5f1`;
the exact resulting source commit is the PR branch tip carrying this record.

## Decision

Accept the public route as a tested synthetic composition seam. Keep it
unqualified for live GUI, MAP01, physical input release, bounded recovery,
independent task success, model-token/latency savings, and matched efficiency.
Continue to keep the source computer-control Issues open until their separate
acceptance evidence exists.
