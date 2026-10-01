# Construction clock 30 — passive process activity

Auditor's original label: `HOLD_PASSIVE_ASYNC_TIC_STATIC_PROCESS_IDLE`.
Corrected interpretation: `HOLD_LIVE_TIC_UNOBSERVED`. Excluded construction
evidence only; formal allocation remains 0/120. See
[`INTERPRETATION_ERRATUM.md`](INTERPRETATION_ERRATUM.md): the child process
sleep state and frozen API snapshot do not reveal the engine's live tic.

## H / T / D / C / U

- H: determine whether the headless ViZDoom process is actively consuming CPU
  while the exposed episode tic remains unchanged during an unadvanced
  `ASYNC_SPECTATOR` MAP01 session.
- T: three fresh Freedoom 0.13.0 sessions in OrbStack Docker, Linux/arm64,
  ViZDoom 1.3.0, 35 Hz, empty available-button set, hidden window, no DISPLAY,
  no network, read-only container root, 128 MiB noexec tmpfs. Each session ran
  `new_episode()`, then a 1.5 s passive sample window. No `advance_action`,
  `make_action`, `set_action`, keyboard, or mouse calls were made. The exact
  current-main `_coherent_progress_sample` was called once after the window.
- D: retain monotonic getter brackets, episode tic, `/proc/<pid>/stat` state and
  CPU counters for the ViZDoom child, `SC_CLK_TCK`, exact scorer trace/span,
  image/WAD identities, and cleanup. The independent auditor verifies row
  cardinality, conditions, unchanged tics, scorer return and process identity.
- C: all 3 sessions initialized, all 3 scorer calls returned and all 3 games
  closed. At 100 process clock ticks/s, child CPU deltas were 4, 2 and 3 ticks
  over 1.56, 1.52 and 1.53 s. Child process state was `S` at the measured
  start/end boundaries. Tic stayed at 1 in all 3; 27/26/26 getter samples. The
  structural audit returned its original hold label with zero audit errors.
- U: low CPU and sleeping boundary states do not establish whether engine
  simulation advanced. The Python-visible tic snapshot is not an independent
  live-tic witness; no 35 Hz rate or scorer phase was measured. It does not
  satisfy #3453's formal gate and cannot be pooled into its 120 rows.

## Reproduction and hashes

OrbStack server 29.4.0. ViZDoom image ID:
`sha256:4320dd483b24ea91c1481f12fd5799c903d9daa99a517b994f607037098ea41d`
(`linux/arm64`). Official Freedoom 0.13.0 WAD SHA-256:
`a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
Network was disabled; root filesystem read-only. Exact probe, runner/runtime
modules and output were mounted explicitly. The command was:

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --workdir /tmp --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1/passive_process_activity_construction.py:/probe.py:ro" \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1/runner.py:/opt/phase-probe/runner.py:ro" \
  -v "$PWD/research/doom/session_map01_v13.py:/opt/phase-probe/session_map01_v13.py:ro" \
  -v "$PWD/research/doom/map01_scorer_stdio_adapter_v1.py:/opt/phase-probe/map01_scorer_stdio_adapter_v1.py:ro" \
  -v "$PWD/research/doom/main_thread_scorer_polling_v1.py:/opt/phase-probe/main_thread_scorer_polling_v1.py:ro" \
  -v "$PWD/research/doom/independent_progress_clock_v2.py:/opt/phase-probe/independent_progress_clock_v2.py:ro" \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1/results/construction-clock-30:/results" \
  -v /tmp/agent-interface-3300-freedoom.rVM7UB/unpacked/freedoom-0.13.0/freedoom2.wad:/assets/freedoom2.wad:ro \
  --entrypoint sh agent-interface-map01-clock-review-fixed:20260920 \
  -lc 'unset DISPLAY; python -u /probe.py'
```

- Probe SHA-256: `906cd0c9f278ddecda74635b4f1d8195d0d2cf8432bfaf3f78e80734dd6d4fa1`
- Raw JSON SHA-256: `b892a8e9fb12a98d3ac8162c2712bdc05cea75c61bcc2bfcb95f01fe0b5cc2cd`
- Auditor source SHA-256: recorded in `invocation.txt`.
- Audit JSON SHA-256: recorded in `invocation.txt`.

The process CPU metric is diagnostic only. It does not change the estimand or
replace the live phase witness. Focused audit tests are retained alongside the
source and are run in the existing isolated arm64 test image.
