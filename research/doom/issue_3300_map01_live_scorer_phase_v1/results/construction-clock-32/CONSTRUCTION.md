# Construction-clock-32 — internal engine tic progress

Disposition: `PASS_CONSTRUCTION_ONLY_INTERNAL_TIC_PROGRESS_API_SNAPSHOT_STALE`.
This is an explicitly instrumented diagnostic; it is not formal allocation
data and remains excluded from #3453's 120 rows.

## H / T / D / C / U

- H: test whether ViZDoom's internal `gametic` advances during a passive
  `ASYNC_SPECTATOR` MAP01 interval when the Python-visible shared `MAP_TIC`
  remains unchanged.
- T: OrbStack Linux/arm64; ViZDoom 1.3.0 image
  `sha256:4320dd483b24ea91c1481f12fd5799c903d9daa99a517b994f607037098ea41d`;
  official Freedoom 0.13.0 WAD SHA-256
  `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
  Three fresh hidden MAP01 sessions, 35 Hz, empty button list, explicit
  `new_episode()`, DISPLAY unset, network disabled, root read-only, 128 MiB
  noexec/nosuid tmpfs. `+viz_debug 2` enables the upstream `VIZ_Tic` print of
  `gametic`/`vizTime`; `stdbuf -oL` makes child stdout lines ordered at the
  parent markers. Each session had a 1.5 s passive window and one exact
  current-main scorer call after the window. No controller tic/update,
  action, keyboard, or mouse message was sent during the window.
- D: independently parse the stdout between passive begin/end markers and
  reconstruct contiguous internal tic numbers; compare with every retained
  Python-visible episode tic and the raw scorer trace.
- C: all 3 sessions showed 52, 52 and 53 consecutive internal `gametic` /
  `vizTime` increments inside the 1.526/1.525/1.549 s windows. These imply
  within-window minimum mean rates of 34.08/34.11/34.22 increments/s (the
  numerator's first and last log events are inside the measured interval, so
  dividing their tic difference by the full interval duration is a
  conservative lower bound). The Python API tic remained 1 in all 3 sessions
  across 27/28/28 reads; the exact scorer returned 3/3 and cleanup succeeded
  3/3. Independent audit: `PASS_CONSTRUCTION_ONLY_INTERNAL_TIC_PROGRESS_API_SNAPSHOT_STALE`,
  zero errors.
- U: debug printf adds output and can perturb scheduling; this proves internal
  progress only in the instrumented construction condition. The stdout event
  ordering gives a count and broad window bracket, not nanosecond edge times or
  sub-tic scorer phase. It does not establish the uninstrumented formal phase
  distribution or authorize the one-shot 120-row allocation.

The corrected predecessor `construction-clock-30` interpretation is in its
[`INTERPRETATION_ERRATUM.md`](../construction-clock-30/INTERPRETATION_ERRATUM.md).
Run 31 is preserved separately as `STOP_LOG_ORDER_UNBRACKETED`; its buffered
stdout could not bracket tic logs to the passive window.

## Reproduction

Exact command, image/WAD provenance and SHA-256 values are in `invocation.txt`.
The historical stdout markers carry the prefix `RUN31` due a reused probe
string; the raw repetition IDs and enclosing directory are run 32, and the
independent auditor binds all three by repetition ID. This harmless label typo
is retained rather than rewriting the capture.

The exact scorer source hash remains
`1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98`.
The environment was instrumented only with the documented ViZDoom debug
setting and line-buffered stdout; the scorer predicate was unchanged.

Auditor implementation SHA-256: `d9a03ebfd3125a7129e3d876f73c8b793c89ffe97ce956b39155219795b167ee`.
Audit JSON SHA-256: `47741b358f9e82e30e047015ace1842e450612d3f9b7eea29351064eea8a4f2c`.
The three focused tests and 23-test combined suite output are retained in
`test-container.log`; test source SHA-256:
`ad83283d1fa926d02a07f057d2196351d0499b67b58aefa5f81aab3f64844fa3`.
See `audit/REPRODUCE.md` for the exact isolated test commands.
