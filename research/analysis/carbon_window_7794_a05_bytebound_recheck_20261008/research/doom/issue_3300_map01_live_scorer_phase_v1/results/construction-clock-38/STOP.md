# Construction-clock-38 — nanosecond trace without post-scorer bracket

Disposition: `STOP_NO_POST_SCORER_TIC_BRACKET`; no phase conclusion.

## H / T / D / C / U

- **H:** Line-buffering the pinned engine's `+viz_debug 2` output will make each `VIZ_Tic` record a separate syscall that `strace` can timestamp in the same container realtime domain as Python clock anchors.
- **T:** Three fresh hidden MAP01 `ASYNC_SPECTATOR` sessions at 35 Hz; passive 1.5 s observation; exact scorer once; no advancing API calls; `strace -f --absolute-timestamps=unix,precision:us -T -s 4096 -e trace=write,writev` around `stdbuf -oL python -u`.
- **D:** Retained the raw scorer/clock trace, container stdout/stderr and strace output. The logger produced individual `VIZ_Tic` writes, but this invocation ended without a post-scorer observation window, so getter events were not bracketed by both preceding and following tic records.
- **C:** This is a capture-instrumentation stop, not a result about scorer phase. The syscall timestamp is after the engine formats its debug message; logger latency was not bounded. No formal phase or 120-row result is inferred.
- **U:** Whether a complete same-clock bracket can be captured with adequate clock-domain and event-time bounds remained open; the separate successor run39 increased timestamp precision but did not add a post-scorer bracket.

Preserve this run as-is. Formal allocation remains 0/120.
