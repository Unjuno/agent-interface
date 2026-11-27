# Win32 live fixture normal-completion horizon experiment r03

Date: 2026-11-10 (Asia/Tokyo)
Source implementation: `0d4f8e323af30df6b7cb17bdbb83563c4a17f6fc`.
Target: repository-owned `Agent Interface Win32 Fixture`, one `A` chord, one public `supervised-win32` MCP session.

## Question and setup

Can the public caller keep the stdio session alive after a `pending` dispatch, observe terminal completion, and retain a bounded late-input horizon on the normal-completion path? Conditions are retained in `conditions.json`; raw public calls/results, producer custody records, fixture events, session close, and timeline are retained alongside this report.

## Observations

- Dispatch returned `pending` at 2026-11-10 20:25:02 JST. The same stdio session remained open while the probe polled `interface_results` until terminal completion at 20:25:07.
- The fixture event stream contained `ready` and exactly one application-visible `char` event with code 97 (`a`). Its file's last-write time was 20:25:05.233495, about 3,233.5 ms after pending returned. The fixture does not timestamp individual messages, so this is a bracket from file metadata, not an exact event timestamp.
- The public terminal result reports action and producer `completed`, input dispatched, release confirmed, verified neutral completion readback, and a 2,000,000,000 ns late-input horizon marked verified. The horizon contains 76 samples; maximum sample gap is 32,000,000 ns against a 100,000,000 ns allowance.
- Persistent custody is `clear` (revision 18) for operation `a691feb96ad84a25944ff7f3f174be3e`; the result's `task_success` remains null and replay is denied. The global asynchronous A-key high bit was up after completion. The fixture accepted `CloseMainWindow` and exited.

## Interpretation and limits

This is one scoped live-fixture demonstration of normal public completion plus finite post-completion observation after a delayed application-visible input. It closes the specific r01 gap where a pending public call lost its registry before a normal-path horizon receipt could be observed. It is not an independent task-success score, GZDoom/MAP01 control, a hard physical-release deadline, continuous neutrality between samples, general reliability, or an efficiency comparison. The file timestamp does not give exact event delivery time. Keep the overall computer-control goal open.

## Evidence

`conditions.json`, `dispatch*.json`, `timeline.json`, `events*.json`, `final-state.json`, fixture source and logs, and all raw MCP directories (including the terminal report and producer records) are retained. `SHA256SUMS` covers all packet files except itself.
