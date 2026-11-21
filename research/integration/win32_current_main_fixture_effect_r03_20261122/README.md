# Current-main Win32 fixture delayed-effect repair check R03

Status: `PASS_SCOPED_FIXTURE_EFFECT` on a fresh native Windows fixture after the receipt-buffer capacity fix.

## Conditions

- Source base: main `6d15df538cff4467a6c72a84a93cfc4557917551`; local checkout included the single buffer-capacity fix and regression test. The public CLI invoked this working checkout.
- Fresh fixture PID 40164 / HWND 27791254. Before dispatch, Computer Use raised that exact window; a separate foreground check confirmed PID/HWND/title match.
- One public `supervised-win32` action with three operations: focus, A key chord, release_all. No provider/model call and no retry.

## Result

- Operation `8eec70741f874c56a21de3d9d097b682`; call `fe4955365d904a42969a82622e4bd795`.
- Public terminal action `completed`; release confirmed true; task_success remains null (no product task oracle); replay false.
- Producer exited with code 0. Per-operation receipt has all three operations `completed`; A key chord recorded 2 SendInput attempts and 2 returned insertions.
- Release receipt reports A key-up returned, no keys/buttons down or unknown, and verified true.
- The completion late-input horizon was 2,000 ms: 77 observations, maximum observed sample gap 32 ms (maximum allowed 100 ms), no late input.
- Fixture event log recorded A keydown accepted, two A keyup deliveries (program release and terminal cleanup), then an independent delayed effect after 6,000 ms with `text="a"`, `verified=true`. The effect occurred after the runtime completion horizon and did not change the terminal action.
- The exact run-owned fixture was closed with Alt+F4 after the MCP session closed and was absent from the UI window inventory. PID absence and effect/event files are in raw.

This validates one narrow public standard-caller fixture task and delayed application effect, plus one 2 s no-late-input horizon. It does not validate GZDoom/MAP01, provider/model use, efficiency, broad reliability, or preview graduation. R01 and R02 remain preserved negative runs; neither was replayed.

See `conditions.json`, `COMMANDS.md`, `source/`, `raw/`, and `SHA256SUMS`.
