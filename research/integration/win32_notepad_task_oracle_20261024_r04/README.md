# Native Notepad transfer and pacing evidence (R04)

## Finding

A freshly opened, blank Windows Notepad window was used to compare rapid Unicode text delivery with the repository's existing bounded text-gap compiler. The calls used the public `interface_observe`, `interface_dispatch`, `interface_verify_task`, and `interface_close` tools, the native `supervised-win32` owner/producer, and an independent Win32 `WM_GETTEXT` task oracle. The tool functions were invoked through the in-process MCP server object; this did not exercise stdio transport or a model-controlled client.

| Condition | Public program | Outcome |
|---|---|---|
| Rapid text | One 20-character `text` op | Dispatch completed and release was confirmed, but Notepad contained `AIRL-202-6CT024-1R04`. The independent verifier returned `verified / task_success=false`. |
| Explicit per-character pacing | One `text` op with `gap_ms=25` | The public API compiled it as `bounded_text_gap`: 20 text operations plus 19 `wait_update` operations. Native dispatch completed with 40 input events and release confirmed. The standard dispatch receipt kept `task_success=null`; the separate verifier returned `verified / task_success=true` for exact text `AI-CTRL-20261024-R04`. |

A manual per-character program with 25 ms waits also passed once in attempt 07. In attempt 09, runtime execution lasted 516 ms (including the declared gaps); the separate release/neutral readback timestamp was 610 ms after execution start, and the independent exact-text read was recorded 641 ms after execution start. Host timestamps are quantized to about 1 ms in this sample. These mark evidence availability, not physical input-to-effect latency or the instant Notepad first rendered the text. The rapid and paced results show an association on this Notepad generation; they do not prove that pacing is the cause across Windows apps or establish a reliability estimate. No speed or efficiency claim is made.

The test window was restored to empty by a separate public dispatch: `Ctrl+A`, wait 50 ms, Backspace, wait 50 ms, release. Its task verifier returned success for the empty document, and a final independent `WM_GETTEXT` read returned zero characters. The window remains open and empty. Other Notepad windows were left untouched.

## Attempt record

All attempts are retained separately. Errors and unknown outcomes remain immutable and are not counted as passes.

- Root packet: public observation succeeded, but the first script checked the outer review envelope. No dispatch occurred.
- `attempt-02/`: first dispatch focus was refused because the target was not foreground; zero backend emissions, release verified, no text change. The task-oracle identifier was malformed, so its verifier result is unknown.
- `attempt-03/`: read-only observation returned; the old parser issue recurred. No dispatch occurred.
- `attempt-04/`: rapid Unicode delivery produced the wrong 20-character string; independent verifier returned task failure. The failure is preserved.
- `attempt-05-cleanup/`: cleanup action completed. The verifier receipt was rejected because the script added 1 ns while host monotonic samples were equal. A direct subsequent text read showed the document empty.
- `attempt-06-paced/`: exact manual-paced string was read independently, but the same artificial +1 ns receipt error made the standard verifier unknown. Its cleanup readback was empty.
- `attempt-07-verified/`: manual-paced text passed the standard task verifier. Cleanup without inter-operation waits did not delete the selected text; that failure is retained.
- `attempt-08-cleanup-paced/`: fresh cleanup with waits passed the standard verifier and ended empty.
- `attempt-09-gap-ms/`: the public `gap_ms=25` compiler path passed exact task verification; cleanup with waits also passed.

Each attempt stores its program, raw tool responses, native reports, screenshots where returned, oracle observations, and result. `SHA256SUMS` covers the packet files. The worktree's runtime source matched `origin/main` at experiment time; this packet introduces no runtime code changes.

## Scope and limits

The target was one newly launched, previously empty Notepad document, HWND 24840738, with one `RichEditD2DPT` edit child. The target generation was `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`. Window identifiers and images stay in this local packet.

This packet now includes one native held-effect recovery diagnostic through the public server tool implementation (R10); see `attempt-10-real-effect-held/ASSESSMENT.md`. Recovery and key-up were observed, and the pinned owner contract commits `recovered` only before the configured deadline; exact elapsed recovery time was not retained. See the assessment and focused cancellation tests. R10 held the producer after `SendInput` returned, so it does not test a hang inside Windows API I/O or prove arbitrary platform-I/O bounds. It is not a real stdio transport test, MAP01/game transfer, matched efficiency result, or broad reliability estimate. No WSLc allocation or Docker operation was used.

## Local verification

- `python -m unittest runtime.cli_v1.test_cli runtime.cli_v1.test_validate_program runtime.core_v1.test_program_enum_types_e9q4 runtime.cli_v1.test_mcp_supervised_win32 runtime.cli_v1.test_win32_standard_producer` — 84 tests, OK, 4 skipped. Focused follow-up `python -m unittest runtime.guarded_win32_v1.test_process_cancellation` — 12 tests, OK.
- Python `pytest` is unavailable in this environment.
- No tracked runtime source was changed.

