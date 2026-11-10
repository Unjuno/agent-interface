# Win32 live fixture queued-message post-horizon dispatch r10

Date: 2026-11-10. Source main: `85849d1f0384f58e55a0c34abacae5797e002a31`. Route: supervised Win32 public MCP dispatch, one `A` key chord, required release, configured 2,000 ms observation horizon.

## Question and controlled schedule

Can an independently observed task effect be separated from native key-state release when the GUI thread holds already queued keyboard messages until after the public call's verified horizon? A repository-owned Win32 fixture continued servicing non-keyboard messages while explicitly removing `WM_KEYDOWN`/`WM_KEYUP` records into a fixture-side list. The supervised action used the public route and completed its release and 2 s horizon. Only after observing the terminal report did the probe request fixture unblock; the fixture then reconstructed and dispatched those records.

## Result

- The producer receipt reports `input_dispatched=true`, `release_confirmed=true`, `task_success=null`, and `replay_allowed=false`. The exact raw terminal is `mcp/6a40007f52314c1e9baccb7670724f64/report.json`; durable producer result is under `mcp/supervised-win32-producers/`.
- Completion readback verified a neutral state over 2,000 ms with 76 samples, maximum sample gap 32 ms (100 ms allowed). Horizon end was monotonic 77,660,968,000,000 ns.
- The fixture recorded an A `WM_KEYDOWN` and two A `WM_KEYUP` messages in its actual queue during the defer interval. After horizon completion, at 77,663,078,000,000 ns (about 110 ms later), it dispatched the reconstructed records to its WndProc.
- The added independent `keydown_effect` oracle did not fire and no effect file was created. Thus this is a post-horizon queued-message dispatch with **no observed task effect**, not a positive effect result. `interface_results` response snapshots in `timeline.json` include earlier `running` snapshots and a final nested completed action; use the raw durable MCP report as the terminal source.
- The session was closed and fixture process exited. The main report is authoritative about release; `interface_close` itself has `release_confirmed=false` because it reports session close, not the already completed action release.

## Interpretation and limits

This is a scoped negative discriminator: queue records acquired during the action/horizon can be deliberately held by this fixture and dispatched later, yet this run did not produce the declared application effect. The experiment does **not** establish spontaneous late OS delivery: the fixture removed the messages from the queue and later manually reconstructed `MSG` records before `TranslateMessage`/`DispatchMessage`. It does not prove GZDoom/MAP01 behavior, product task success, a physical release deadline, continuous neutrality between samples, general reliability, or efficiency. Keep the broader goal open and do not replay the consumed action.

Conditions, fixture/probe source, event stream, public MCP requests/reports, producer result, timeline, observation image, terminal snapshot, process/session cleanup records, and `SHA256SUMS` are retained in this directory.
