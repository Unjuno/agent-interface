# Construction-clock-50 — exact scorer in uninstrumented source control

## H/T/D/C/U

- **H:** The exact current-main `_coherent_progress_sample` may behave differently in a pinned uninstrumented ViZDoom source build than in run45–48's instrumented builds during passive async execution.
- **T:** In six fresh OrbStack Docker containers, use the run49 control image (ViZDoom 1.3.0 pinned upstream source with the run48 patch reversed and zero CNTVCT opcode). Run hidden 35 Hz MAP01 `ASYNC_SPECTATOR`, passively poll `get_episode_time()` for 1.5 s, invoke the exact current-main scorer exactly once, passively poll another 0.5 s, then close. Make zero action/advance calls. Retain every getter value and monotonic boundary, API tic trace, result, setup/cleanup and image/source/WAD identity. Stop each row on identity/setup failure; no replacement.
- **D:** Retain six independent raw rows and stdout logs. Independently check exact eight-getter order, coherence/tic values, scorer return, passive-window read counts, zero action calls, environment hashes, and cleanup. This tests scorer behavior but does not reconstruct phase without an independent engine-edge witness.
- **C:** Construction-only public-API/scorer observation on this one pinned arm64 OrbStack/Freedoom fixture. No internal uninstrumented tic trace exists, so API changes do not alone establish engine progress or true scorer phase. Six sessions are not the frozen 120-row allocation.
- **U:** Whether uninstrumented public snapshots remain stale and whether the exact scorer returns coherent samples in this fixture are unknown before execution. Formal allocation remains 0/120.

## Frozen schedule

Six one-shot sessions, seeds 349500–349505, each on a new container. Configuration is hidden/no-sound/no-button `ASYNC_SPECTATOR`, configured ticrate 35, 350-tic episode timeout. Passive windows are 1.5 s before and 0.5 s after exactly one scorer call. No retry or action advancement. Raw rows append to `raw.jsonl`; each stdout is separately retained.

## Observed result

All six uninstrumented control sessions initialized and closed. The exact current-main scorer returned 6/6; its eight getter calls had the exact expected sequence, both episode-time getters were `[1,1]`, and the returned kills/deaths/finished/dead/map-exit fields agreed with the raw getter results. Each session had 115–120 pre-scorer reads and 38–40 post-scorer reads; all observed API tic values remained 1. Independent audit: `PASS_CONSTRUCTION_ONLY_UNINSTRUMENTED_EXACT_SCORER`, six rows, zero errors, including source/WAD/binary identities, actual passive-window spans, getter order/bounds, result reconstruction and cleanup.

This directly confirms only that the unchanged exact scorer returns a coherent tic-1 sample under this six-session uninstrumented construction fixture. It does not establish an advancing uninstrumented engine, phase distribution, or a formal score reliability rate. Run49's separate uninstrumented control pair2 did observe API tic 2, so passive snapshot progression is variable across sessions. No formal rows were consumed; #3453 remains 0/120.
