# Construction-clock-42 — independent repeat of direct tic-entry clock correlation

Disposition: `PASS_CONSTRUCTION_ONLY_ENTRY_CLOCK_CORRELATION`.
Formal allocation remains **0/120**.

## H / T / D / C / U

- **H:** The source-instrumented same-`CLOCK_MONOTONIC` construction probe from run41 reproducibly places exact scorer getter calls between successive ViZDoom tic-entry-nearby samples on a separately rebuilt pinned image.
- **T:** Three fresh hidden MAP01 `ASYNC_SPECTATOR` sessions, 35 Hz, 1.5 s passive window, exact scorer once, no action-advancement calls, 150 ms post-scorer window, and cleanup. Uses the final Dockerfile build recipe, pinned ViZDoom 1.3.0 source commit/submodule, the same instrumentation patch, and official Freedoom 0.13.0 WAD. Runtime is Linux arm64 `--network none --read-only` with tmpfs and a writable result mount.
- **D:** 3/3 initialized, scorer returned and cleanup completed; passive API tic remained 1 in each repetition. Recorded 64/66/64 contiguous `vizTime` entries. Independent v2 audit produced zero errors and bracketed all 24 getter starts. Median entry intervals were 28.972/28.363/28.703 ms. Per-repetition getter phase-fraction ranges were 0.246–0.265, 0.654–0.669 and 0.533–0.538. Getter call spans ranged 6.126–82.337 µs, 3.125–47.668 µs and 1.292–21.501 µs. Corrected auditor tests pass 2/2.
- **C:** This repeat confirms the instrumentation/build path operates again, but the 3-per-run getter phase ranges differ from run41, as expected for phase sampling. The clock read still occurs after a helper call at function entry, and both helper/read latency and append-write scheduling perturbation are unbounded. Consequently this remains construction-only; it does not satisfy the exact ±1 ns/µs boundary witness or formal allocation requirements.
- **U:** Whether the source timestamp uncertainty can be quantified sufficiently, and whether the modified engine preserves the target uninstrumented timing distribution, remain unresolved. No formal 120-row collection is authorized by this result.

Run42 is a fresh repeat, not pooled with run41. Its original v1 auditor label was regenerated from unchanged raw with the v1 auditor baked into the hash-identified image; both that output and post-hoc v2 audit, container log, tests, and invocation are retained and hash-bound below.
