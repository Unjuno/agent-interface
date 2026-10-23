# Public Win32 caller: old UNKNOWN and fresh scored generation — R04

R04 composes two target generations through the opt-in public MCP route on source commit `967e8f65c89e302e85ed218919a45246beeaaa1a`.

Generation A starts a gated producer and is canceled. Its recovery helper sends a receipt bound to the wrong operation, so the retained cancellation is `UNKNOWN`, release remains unconfirmed, task success stays null, and replay stays denied. A fresh MCP server/session then binds generation B and starts a distinct action. A separate application-simulator process updates task state; a distinct oracle process scores that state using a different oracle ID and returns a generation-B receipt with `task_success=true`. A final lookup confirms generation A's retained result is unchanged.

The focused Win32 adapter/public-composition/cancellation suite passed 25/25 in normal and optimized CPython 3.11.9. Raw outputs are [`raw/normal.log`](raw/normal.log) and [`raw/optimized.log`](raw/optimized.log); conditions and source fingerprints are in [`CONDITIONS.json`](CONDITIONS.json).

This is synthetic process-ordering evidence, not a live application result. It does not qualify native `SendInput`, physical release, late-DOWN exclusion, exclusive desktop input ownership, MAP01, matched efficiency, or reliability. No WSLc allocation, Docker use, or native input occurred; Issue #7924 remains STOP/HOLD.
