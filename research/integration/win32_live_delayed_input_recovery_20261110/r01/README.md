# Win32 live fixture recovery experiment r01

Date: 2026-11-10 (Asia/Tokyo)
Source implementation: `cecb81c5819815fd8a13ebfee460914286d22765`
Target: repository-owned `Agent Interface Win32 Fixture`, HWND 10881668, PID 32184.

## Question and setup

Can the public supervised-Win32 MCP route deliver a task key after the caller has received `pending`, and can a fresh server recover the retained input custody with a finite late-input horizon? One fresh fixture, one `A` key chord, one 2,000 ms configured horizon. No GZDoom/MAP01 executable was present; this is fixture evidence only.

## Observations

- Native observation matched target generation `3c52d0aefbc473ebb28b2fe88a1509860c0ae52365cefe1f39e414cecde92c8a`.
- Standard `interface_dispatch` returned `pending` after its 5,000 ms wait: worker running, backend attempted, result unavailable, release unconfirmed, task effect unknown, replay denied.
- The original event snapshot at 3 seconds contained only `ready`. A later additive capture found one `char` event with code 97 (`a`). The fixture does not timestamp individual messages, so the precise delivery time is unknown; it occurred after the pending response and demonstrates a delayed application-visible effect.
- Durable producer result later showed normal completion, three emissions (two program emissions plus release), a verified native release receipt, and no keys/buttons down. It did not contain a late-input horizon receipt. The public caller receipt was unavailable after its server process ended; durable custody therefore correctly remained unresolved.
- The exact registered producer identity was absent. The fresh recovery session matched source operation, target generation, and `key:fixture:A`, performed bounded native release/readback, and sampled for 2,000,000,000 ns. It returned `recovered`, `release_confirmed=true`, neutral readback, 77 samples, 32,000,000 ns maximum observed gap against 100,000,000 ns allowance, and `late_input_horizon_verified=true`.
- Durable custody is now `clear`, revision 6, with this operation/generation as last resolved. Source action remains `unknown`; task success remains null; replay remains denied; next action requires a fresh generation. The owned fixture was closed through its main window and exited.

## Interpretation and limits

This is a successful, finite live Win32 input-release/recovery and delayed-effect discriminator on a repository-owned fixture. It shows that application-visible input may arrive after a public pending response. It does not prove a hard physical release deadline, uninterrupted neutrality between samples, task success, MAP01 control, GZDoom behavior, broad reliability, or efficiency versus a baseline. Do not replay the source action. Retain the UNKNOWN source outcome.

## Evidence files

`conditions.json`, initial observation and raw dispatch (`observation*.json`, `dispatch*.json`, `dispatch-r01.log`), both event snapshots (`events-post-horizon.json`, `events-post-horizon-late.json`), exact producer receipt under `mcp/supervised-win32-producers/`, `source-custody-record.json`, preflight status, and `recovery-result.json` plus `recovery-r01.log`. `final-state.json` records cleanup. `SHA256SUMS` covers this run packet, excluding itself.
