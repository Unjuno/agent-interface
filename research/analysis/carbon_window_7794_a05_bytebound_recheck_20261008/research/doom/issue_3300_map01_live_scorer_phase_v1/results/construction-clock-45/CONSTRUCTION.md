# Construction-clock-45 — passive async progress with exact scorer

Status before run: construction-only, excluded from the frozen 120-row allocation.

## H / T / D / C / U

- **H:** A fresh hidden `ASYNC_SPECTATOR` MAP01 session at 35 Hz, with no action-advancement calls, exposes tic progress during a passive 1.5 s interval; the unchanged `_coherent_progress_sample` then returns against that ordinary async session.
- **T:** Three fresh isolated game processes in the pinned arm64 ViZDoom 1.3.0 instrumentation image and official Freedoom 0.13.0 WAD. In each process: explicit episode start, mode/ticrate/buttons readback, 1.5 s passive `get_episode_time()` polling (no `advance_action`/`make_action`/`set_action`), one exact scorer call, shutdown. `VIZ_Tic` source-clock records are retained per process. Docker is network-disabled/read-only with only output tmpfs and read-only source/WAD mounts.
- **D:** Retain every timed getter sample, scorer result/error, engine source-clock record, game setup/readbacks, cleanup status, container log, invocation and SHA-256. Report API-tic movement and engine-entry count/rate separately. A construction auditor checks trace record shape/order, rate, session identity, and whether scorer getter values are enclosed by source-clock records; it cannot promote this to formal phase evidence.
- **C:** This tests the literal passive async-clock/scorer compatibility question on one pinned fixture. Source instrumentation remains and its function-entry latency is not bounded. Three rows are construction-only and cannot be pooled into the one-shot schedule.
- **U:** Whether the instrumented clock trace preserves uninstrumented phase/span distribution and resolves the frozen nanosecond boundary neighborhoods remains unknown. Formal allocation stays unauthorized unless the exact phase-uncertainty gate is separately satisfied.

## Observed result (construction only)

The first complete three-session run retained the scorer return and source tic-entry trace but did not retain individual scorer getter boundaries. It is preserved as `raw.jsonl` and is not used for the independent decision below. Two earlier import-only attempts are retained as stderr logs; neither started a game.

The corrected, separately rebuilt three-session allocation retained all scorer getters in `raw-with-getter-trace.jsonl`. All 3/3 sessions initialized, returned the unchanged exact scorer after one coherence attempt (8 getter calls; two `get_episode_time` values), and closed cleanly. In each session, 118–119 passive API reads over about 1.49 s returned `episode_tic=1` only. Meanwhile, the instrumented `VIZ_Tic` trace contained 57 contiguous `vizTime` records per process, with median rates 34.012, 35.260, and 35.433 Hz. The entry trace overlapped 99.45%, 100%, and 99.58% of the passive read windows. Each exact scorer's two tic reads also returned 1.

The last instrumented entry sample preceded the first scorer getter by 14.54–19.99 ms, with no following edge in the captured trace; the exact scorer phase is therefore **not identified**. The source timestamp is after compiler prologue and every-tic instrumentation can perturb scheduling. Independent reconstruction in `audit.json` yields `PASS_CONSTRUCTION_ONLY_ENGINE_PROGRESS_API_TIC_STALE`, zero audit errors. This is positive evidence that the hidden async engine's internal tic loop advanced at approximately the configured rate while the public episode-time API and exact scorer remained at tic 1 in this fixture. It is not a phase/span distribution, does not satisfy #3453's formal T, and does not authorize the one-shot schedule; formal rows remain 0/120.

The next experiment must resolve or explicitly route around this API/source clock mismatch without action advancement and without assuming source instrumentation preserves target phase. Preserve all runs as disjoint evidence. Hashes are recorded in `SHA256SUMS.txt`.
