# Kernel hardware breakpoint clock witness probe — construction only

Disposition: `PASS_BREAKPOINT_TIMESTAMP_CONSTRUCTION_ONLY`. This is a new read-only witness-method construction result; #3453 remains `HOLD_LIVE_SPAN_UNIDENTIFIED`, formal allocation remains 0/120.

## H / question

Can a Linux hardware execute breakpoint on the exact running ViZDoom engine's `VIZ_Tic()` entry, opened with only `CAP_PERFMON`, yield monotonic kernel timestamps that bracket a call to the unchanged current-main MAP01 scorer, without inserting code into the engine?

## T / experiment

- OrbStack Linux/arm64, kernel 7.0.14, `--network none --cap-add=PERFMON`; no `SYS_ADMIN`, `--privileged`, model, or input actions during the capture window.
- Runtime Python package reported ViZDoom 1.3.0. The engine executable was an unmodified Release build from source commit `c8e0a31182d98c6f40a65674283e736b851e8e59`, with debug symbols/link map but no source instrumentation. Its exact binary SHA-256 was checked on the running child before attaching the event.
- The baseline binary was mounted read-only over the package engine path. `VIZ_Tic()` link address `0x3eee80` plus the verified ELF load bias `0xaaaae66b0000` resolved runtime address `0xaaaae6a9ee80`; the address was inside the mapped executable region.
- A `PERF_TYPE_BREAKPOINT` / `HW_BREAKPOINT_X` event sampled `PERF_SAMPLE_IP|TID|TIME`, selected `CLOCK_MONOTONIC`, with a 4-byte instruction breakpoint. It was enabled for a 659.1 ms passive interval. The exact current-main `_coherent_progress_sample` (source SHA-256 `1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98`) was called once while the event was enabled. No `advance_action` occurred during the capture interval; one startup refresh happened before it.

## D / independently audited observations

Independent stdlib audit: `PASS_BREAKPOINT_TIMESTAMP_CONSTRUCTION_ONLY`, 23 samples, zero errors, zero lost/non-sample records. All 23 kernel sample IPs exactly matched the runtime `VIZ_Tic()` address and all sample PID/TID values matched the engine child. Sample timestamps were strictly increasing and the measured event rate was 34.953847/s. Inter-event spans: 23.703–33.356 ms, median 28.606 ms.

The exact scorer's outer call spanned 60,084 ns. The last recorded event preceded scorer start by 9.302 ms; the next followed scorer end by 20.310 ms. Thus the *recorded kernel-event timestamps* bracket this call with a 29.672 ms interval. At capture start/end, Python `perf_counter_ns` and explicitly selected kernel `CLOCK_MONOTONIC` differed by −2.208 µs and +3.584 µs, respectively. The public API tic snapshot stayed 1367 before and after, even though VIZ_Tic-entry events were recorded.

## C / scope and interpretation

This shows a concrete way to observe exact engine function-entry PCs and kernel timestamps without patching the running executable. It does not prove that the engine's MAP_TIC simulation state advances (the API snapshot remained stale), nor that the `PERF_SAMPLE_TIME` timestamp equals the hardware instruction-entry time. Breakpoint exception delivery latency and measurement-induced scheduling perturbation have not been bounded. The 29.672 ms recorded-event bracket is not a sub-nanosecond phase estimate and cannot certify the frozen boundary-neighbor cases. Treat this as a promising witness candidate, not the independent non-perturbing clock gate required for formal allocation.

## U / next gate

Calibrate `PERF_SAMPLE_TIME` delivery latency against an independent in-engine counter on excluded sessions; quantify breakpoint-on/off scheduling and event-loss effects; capture all exact scorer getter start/end brackets against these edge timestamps across fresh sessions. Then independently reconstruct phase uncertainty and verify it is narrow enough for the preregistered phase boundaries. Only after that may a frozen one-shot allocation be considered. If delivery or perturbation uncertainty remains too wide, retain a HOLD and do not substitute action-driven samples.

## Provenance

- Raw full record: `raw.json`, SHA-256 `c8ec27f4a19222f82411bc0b2f4b4e5ec147a04b4e0b5a43c0d76ccf0442dfad`.
- Independent audit: `audit.json`, SHA-256 `1a02258d60f550826359d0677eab25e294ba5b3cb39bef9b8dbd736a9e8fc954`.
- Executed runner: `map01_hwbp_probe.py`, SHA-256 `666f477cd148b1ede2e21886b36968975c9d5e3e963f38554597f19c528e1387`.
- Independent auditor: `audit_map01_hwbp_probe.py`, SHA-256 `be2ba50bb237dd365ad2008a32827cf650f0c503177b0f00431ac9aeb85df548`.
- Source-build binary SHA-256 `df948feffe93a27345f02eec891f85d89841a927c6062999b9a42a84f0db40b2`; linker map SHA-256 `add5dca83f2be7669f5d5a350fbbab97097e8a616aa4b64f07c6598e88e2b057`.
- Fixture manifest/save/WAD SHA-256 values are retained in `raw.json`; the scorer, clock and adapter dependency hashes are in `source-manifest.json`.
