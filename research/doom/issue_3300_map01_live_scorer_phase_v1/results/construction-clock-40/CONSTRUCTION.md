# Construction-clock-40 — same-clock logged-tic correlation

Disposition: `PASS_CONSTRUCTION_ONLY_SAME_CLOCK_TIC_LOG_CORRELATION`.
Formal allocation: **not started; 0/120 rows**.

## H / T / D / C / U

- **H:** A post-scorer observation window and nanosecond `strace` timestamps can place each getter call of the unchanged MAP01 scorer between adjacent, individually written `VIZ_Tic` debug records, mapped into Python's monotonic clock by paired realtime/monotonic anchors.
- **T:** Three fresh hidden MAP01 `ASYNC_SPECTATOR` sessions on the pinned ViZDoom 1.3.0 / Freedoom 0.13.0 fixture at 35 Hz. Each had a 1.5 s passive window, one exact scorer invocation, zero advancing API calls, and a 150 ms post-scorer collection window. `strace -f --absolute-timestamps=unix,precision:ns -T -s 4096 -e trace=write,writev` wrapped line-buffered engine output. Docker used Linux arm64, `--network none --read-only`, tmpfs `/tmp`, and read-only source/WAD mounts.
- **D:** Three sessions initialized, scorer returned, and cleanup completed (3/3). API tic stayed 1; each passive interval had 29 samples. The trace contained 194 `VIZ_Tic` write events overall; each session had 59 contiguous logged tic values. Median logged-write intervals were 28.764, 28.570, and 28.762 ms. All eight scorer getters in each repetition fell between adjacent logged tic records. Independent audit: zero errors, formal flag false; focused audit suite: 27/27 passed. The initial synthetic fixture test failure is retained unchanged in `tests.txt`; corrected fixture evidence is separately retained in `tests-correction.txt` (2/2), and the focused suite is `all-focused-tests.txt`.
- **C:** This is only construction evidence that same-clock log correlation is feasible. `strace` timestamps the write syscall after `VIZ_Tic` formats its message, not function entry; pre-syscall logger latency is unbounded here. `strace`/ptrace and debug logging perturb scheduling. Realtime-to-monotonic offset widths observed over all anchors were 39,205, 46,289, and 29,332 ns; local scorer-anchor widths were 7,124, 1,458, and 1,834 ns. Anchors do not prove absence of clock steps between samples. Therefore these are positions relative to logged messages, not validated engine-edge phase intervals; no ±1 ns / ±1 μs boundary resolution or formal distribution is claimed.
- **U:** Whether a direct, low-overhead engine tic-entry timestamp can yield an independently bounded phase witness remains unknown. The planned phase allocation must stay held until that witness is validated. Next construction path: instrument the pinned ViZDoom source at `VIZ_Tic` function entry with a monotonic timestamp, retain exact source/build provenance, and compare instrumentation perturbation; do not infer phase from current syscall timestamps.

The auditor reports `PASS_CONSTRUCTION_ONLY_SAME_CLOCK_TIC_LOG_CORRELATION`, not a formal pass. Do not run the 120-row collection from this result. Historical runs 38 and 39 remain STOP records; none is overwritten or pooled.

## Hash-bound reproduction

`audit-recheck-correct.stdout.txt` is a fresh container rerun against the retained raw and strace files; it reproduced the construction-only decision with zero errors. `audit-recheck.stderr.txt` preserves an initial invocation with an incorrect option-style CLI (exit 2); `audit-recheck-correct.stderr.txt` is the successful invocation's stderr. These are tooling records, not experimental observations.
