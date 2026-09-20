# Construction-clock-39 — microsecond bracket attempt still lacks post-scorer witness

Disposition: `STOP_NO_POST_SCORER_TIC_BRACKET`; no phase conclusion.

## H / T / D / C / U

- **H:** Increasing `strace` absolute timestamp precision to nanoseconds, while preserving the line-buffered logger, may resolve scorer getter positions relative to neighboring engine tic records.
- **T:** Three fresh hidden MAP01 `ASYNC_SPECTATOR` sessions at 35 Hz; passive 1.5 s observation; exact scorer once; no advancing API calls; `strace -f --absolute-timestamps=unix,precision:ns -T -s 4096 -e trace=write,writev` around the Python probe.
- **D:** Retained raw output, container log, and syscall trace with checksums. The run still did not collect a post-scorer tic window, so the scorer getters cannot all be bracketed by neighboring tic records. Nominal timestamp resolution alone does not repair the missing event bracket.
- **C:** Instrumentation-only stop. Even a complete syscall bracket would locate formatted log writes rather than `VIZ_Tic` function entry; logger delay and ptrace perturbation are not bounded. No formal phase distribution is inferred.
- **U:** Whether a post-scorer collection window plus stronger event-time instrumentation could bound phase remained unknown; run40 was separately designed to add that window.

Formal allocation remains 0/120. Run40 is a distinct additive experiment; these files remain unchanged.
