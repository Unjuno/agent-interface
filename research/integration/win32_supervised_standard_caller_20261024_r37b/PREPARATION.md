# R37 preparation

R37 combines one fresh bounded-release attempt with one conditional fresh-target
task attempt. The source under test is current main `5c907bb27f30b055180d3b9cdf7a4b706b1ff34f`.
The historical R36 and R03 raw/result hashes are pinned in `conditions.json`;
their attempt outputs are not reused.

The first R37 input-free preflight is preserved in sibling packet `r37` and
failed because the copied runner selected the wrong repository-root parent. It
sent no input; R37b corrects the root calculation and freezes new source hashes,
attempt ID and task token.

Before input, `preflight_r37.py` checks the exact source commit, tracked-tree
cleanliness, runtime and packet hashes, predecessor hashes, absent output paths,
the MCP SDK, the hook-timeout registry value, and that the trace instrumentation
imports without sending input. `run_r37.py` is one-shot. It executes one strict
R36-shaped cancellation attempt; its unchanged release audit gates the second
phase. Only a strict phase-1 pass permits one new fixture/session, one task
dispatch and one independent oracle call. The phase-2 runner retrieves only the
exact call ID and never re-dispatches.

The task result must bind its call ID, operation ID, fresh target generation and
oracle ID. Its observation, validation, dispatch, effect readback, oracle time,
release and cleanup are preserved. The combined audit compares phase times on
the same host monotonic clock. A phase-1 failure remains a retained outcome and
does not launch phase 2.
