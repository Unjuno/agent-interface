# Construction-clock-52 — uninstrumented passive-wait time course

## H/T/D/C/U

- **H:** In the uninstrumented pinned MAP01 control, public episode-time snapshot and exact scorer output may depend on elapsed passive wait duration; specifically, the run49 isolated tic=2 observation may appear near or after the configured 350-tic timeout.
- **T:** Six fresh network-none OrbStack containers use the run49 no-patch ViZDoom image and exact current-main scorer. Wait 0.5, 2, 6, 10, 14, or 20 s with only `get_episode_time()` polling every 100 ms; then record one final finished/tic read and call the unchanged scorer once. No buttons/actions/advancement. Each seed is unique; timeout is 350 tics at configured 35 Hz. Record each passive read, final API values, exact getter brackets, scorer result and cleanup.
- **D:** Retain all six traces and stdout logs. Independent audit checks delay coverage, actual wait/read spans, exact getter order/results, coherent tic, API evolution, fixture/source/WAD/binary identities, no action calls, and cleanup.
- **C:** This is a time-course characterization of public snapshots and scorer on one uninstrumented arm64 container fixture. It does not independently witness engine ticks or phase; delayed samples may encounter episode timeout. It is not the 120-row formal schedule.
- **U:** Whether longer passive waits cause public snapshots or scorer decisions to refresh in the uninstrumented build is unknown. Formal allocation remains 0/120.

## Frozen cells

Ordered cells: 0.5, 2, 6, 10, 14 and 20 seconds; one fresh session per cell; seed 349600 + row index; timeout 350 tics; no retries. These are construction-only diagnostic delays, not requested phase targets.

## Observed result

All six cells initialized, completed the requested passive duration, returned from the exact scorer and closed. Passive reads per cell were 5, 19, 58, 94, 132 and 187. Across the 20 s maximum window, every `get_episode_time()` sample remained 1 and every `is_episode_finished()` remained false; the final public tic was 1. All six exact scorer calls returned with getter tic bracket `[1,1]`. Independent audit: `PASS_CONSTRUCTION_ONLY_UNINSTRUMENTED_SCORER_TIMECOURSE`, six rows, zero errors.

This rules out only a simple short-wait explanation for the public tic-1 snapshot in these six uninstrumented sessions, including across the configured 350-tic timeout interval. It does not establish whether the uninstrumented engine advanced internally; no independent engine edge was available. The single API tic=2 control observation in run49 remains a discordant retained datum. Do not infer a phase distribution or formal scorer failure rate; formal rows remain 0/120.
