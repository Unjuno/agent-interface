# Win32 live fixture application-effect-after-horizon experiment r07

Date: 2026-11-10 (Asia/Tokyo). Source route: `supervised-win32`, main `002947dcc55a9f7ebd56fcccc35af328cfabca04`.

## Question and setup

Does a verified finite native input-release horizon imply that the task effect has already occurred? On a fresh, responsive repository-owned Win32 GUI fixture, the public MCP route sent one A key chord followed by required release. The fixture accepted the real `WM_KEYDOWN`, deliberately withheld `WM_CHAR` translation, and scheduled its independent application effect with a 6,000 ms GUI timer. No action was replayed.

## Result

- Public dispatch returned `pending`, then the same session reported action `completed`, `release_confirmed=true`, verified neutral readback, and a verified 2,000 ms late-input horizon (77 samples, maximum gap 32 ms).
- The fixture independently logged one A keydown and received the key-up messages. After the native horizon was complete and the public terminal result had been observed, its GUI timer wrote `effect.json` and an application-visible `a` effect.
- The delayed effect occurred 6,015 ms after the fixture accepted keydown and 3,953 ms after the horizon ended. Persistent custody subsequently read `clear` at revision 36, with `last_resolved` matching this operation. The fixture and MCP session were closed.
- The public action keeps `task_success=null`; replay remains denied. The fixture's effect file is independent evidence for this declared synthetic task, not a configured public task oracle.

## Interpretation and limits

This is a scoped positive observation that a real GUI application's asynchronous effect can follow a verified input-neutrality horizon. It shows why input release/horizon and task completion must remain separate. It does **not** show that Windows delivered a stale key event after the horizon: the fixture accepted keydown before release and intentionally delayed its own effect with a timer. It is not GZDoom/MAP01, a task-success certificate for a product task, a hard physical-release deadline, continuous neutrality, general reliability, or efficiency evidence.

The exact input route, timer condition, event stream, effect artifact, raw MCP request/results, producer receipt, horizon/custody record, close result, and cleanup are preserved. `SHA256SUMS` covers this packet except itself.
