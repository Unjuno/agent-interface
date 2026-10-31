# MCP cancellation: post-terminal review gate

Base main `3ca68d5d6810b0f54126e4417ca00f758a81dc64`. Two independent fresh WSLc allocations run Calc in private Xvfb with a pinned image, one CPU and network disabled. After typing values, Calc is SIGSTOPed; an MCP guarded call sends Ctrl+S, waits two seconds and then would send F2. The caller polls the same call ID without replay. A subsequent, distinct F3 input through the same alias tests whether the session admits new work. This is an intentional probe, not a replay of the interrupted call.

| Allocation | Condition | First call | F3 probe | File while stopped / after resume |
| --- | --- | --- | --- | --- |
| a06 | no cancel; initial harness | completed | completed | blank / saved |
| a07 | cancel; initial harness | execution failed | refused | unavailable: harness raised on MCP isError |
| a08 | no cancel; corrected harness | completed | completed, 2 program emissions | blank / saved |
| a09 | cancel; corrected harness | execution failed during wait | refused, WINDOW_REVIEW_REQUIRED, no input dispatched | blank / saved |

The original harness incorrectly treated the expected MCP error response for a refused probe as a fatal transport error. a07 is preserved and is not counted as a full effect observation. a08 and a09 use the same corrected response handling. Both final file snapshots were independently parsed by `python audit.py` for the first two cell values (731 and 864); they are not inferred from input or release. In a09 the first call's release receipt is verified with no held keys/buttons, while the saved effect still appears after Calc resumes. Releasing input and blocking further work do not undo earlier input. No claim is made about all possible later effects or other environments.

Each archive retains trial inputs, script, condition, image, top-level receipts, and file snapshots. Nested private receipt journals remain local; their paths, sizes and SHA-256 hashes are recorded in each archive. The two paired samples are evidence for this bounded test, not a reliability estimate, latency guarantee, MAP01 result, or full system completion.
