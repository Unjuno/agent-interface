# Win32 supervised standard-caller R52–R53 public evidence summary

This packet preserves the two outcomes between R51 and R54/R55 without publishing local host, path, process, or window identifiers. Their private experiment packets remain in their original locations. Neither failure was rerun or rewritten.

Both attempts used source commit `0f6464adbb4d2c7331b8aae71ee148a638c0ae79`. The six runtime files pinned by their preflight records are unchanged through current main `d95430720c6396227772f8d4b3cc7e4e8b245ba3`.

R52 is a `NO_INPUT_PRELAUNCH_STOP`. Its input-free preflight passed 15/15. The owned fixture started and exited cleanly, but Computer Use foreground activation could not be obtained. No public dispatch or cancellation was sent, no input/effect was recorded, and phase 2 did not start. The strict phase-1 release audit is 1/11 and the paired audit is `FAIL_OR_UNKNOWN` 1/14; these scores describe the stopped packet, not a failed release mechanism.

R53 passed the input-free preflight 18/18 and the phase-1 strict release audit 11/11. One public dispatch and one cancellation were used. The injected Q-up callback remained held for 1,403.6837 ms after the cancel response; 90 exact-call polls covered the hold. Recovery Q-up returned at +637.0034 ms, and an independent same-generation observer first saw Q-up at +641.936 ms and recorded 73 eligible samples before the callback returned. The fixture's click and save were before cancellation and its text was empty, so phase 1 is not task success.

R53 then entered phase 2 after the release gate, but the new fixture did not receive a Computer Use activation receipt before the bounded timeout. No phase-2 dispatch, cancel, task effect, or timing sample occurred. Fixture cleanup and foreground restoration completed. The combined audit remains `FAIL_OR_UNKNOWN` 3/14; the phase-1 scoped release pass is retained independently.

The public R52 manifest has 24 entries and all match. Its separate private-original manifest has 20 entries and all match its recorded digest. The R53 manifest has 43 entries and all match. Raw private host/path/process/window metadata is retained locally and is not represented as publicly auditable. R54/R55 are later fresh attempts with strict release and fresh-generation task-oracle passes; see the [R54/R55 packet](../win32_supervised_standard_caller_20261024_r54_r55_public/README.md). These attempts remain separate and are not pooled into a reliability estimate.

These results do not establish WSLc behavior or allocation eligibility, MAP01/real-app transfer, matched efficiency, broad reliability, or a hard real-time release bound.
