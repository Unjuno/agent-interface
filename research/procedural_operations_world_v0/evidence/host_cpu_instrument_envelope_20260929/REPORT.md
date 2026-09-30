# Headless CPU instrument envelope — construction result

Issue #5206 · allocation `opsworld-host-cpu-envelope-5206-20260929-01`
Main freeze `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`
Branch `research/opsworld-instrument-overhead-5206-20260929`

## H / T / D / C / U

**H.** At the README-documented maximum moving-object/watcher/assembly load,
the headless simulation+software-render loop and reset primitive may remain
within a 16.667 ms CPU budget.

**T.** On WSL2 Arch Linux, GCC 16.1.1, compile with `make clean all`, run
`make test`, then execute the two README-documented benchmark commands exactly
once each. Both use seed 42, family key 99173, 64 watchers, disabled alert
obligations/event generation, 64 moving objects and 12 assembly pieces. Raw
stdout/stderr, construction log, source pins and hashes are adjacent; full
manifest is `MANIFEST.json`.

**D.** `PASS_CPU_INSTRUMENT_ENVELOPE_ONLY`. Warning-enabled native build and
validity suite succeeded (20/20). The 10,000-frame measurement executed all
frames at 0.1228 ms/frame (8,140.05 frame/s), state hash
`bbc3f6446ab4c0b0`. The 100,000-reset measurement completed at 19.889
microseconds/reset (0.019889 ms/reset). Both are far below the preregistered
16.667 ms primitive budget. Independent readout audit has zero errors and
returns the same scoped disposition.

The budget is only a coarse 60-Hz frame-period ceiling, not an end-to-end
controller latency or performance target. These measurements show the
headless world primitives are inexpensive on this host under the fixed stress
configuration; they do not establish that benchmark instrumentation overhead
is negligible relative to any agent/controller.

**C.** Exact source freeze and identical seed/family/stress settings were used;
only the measured primitive/sample count differs. The separate standard-library
auditor checks exact denominators, finite nonnegative timings, and state-hash
format. Its 5 construction tests reject a wrong count, NaN, malformed hash,
duplicate metric, and accept the expected synthetic control. No GUI, model,
CUDA, GPU, provider, external input, or Docker was used.

**U.** One Windows/WSL2 host, GCC 16.1.1, one authored seed/family and one
measurement per primitive. `--bench-frames` combines `ow_step` and
`ow_render`; `--bench-resets` measures initialization. Event generation and
alert obligations were disabled; controller, host scheduler, X11 presentation,
input delivery, instrumentation/harness overhead, paired baseline, variance,
other operating systems, and held-out tasks were not measured. This is a
construction-only contribution; Issue #5206's formal benchmark HOLD and
promotion gates remain open.

## Exact outcomes

```text
bench_requested_frames=10000
bench_executed_frames=10000
wall_seconds=1.228494
frames_per_second=8140.05
ms_per_frame=0.1228
state_hash=bbc3f6446ab4c0b0
```

```text
bench_resets=100000
wall_seconds=1.988930
resets_per_second=50278.30
us_per_reset=19.889
```

The command tool returned exit code 0 for the build/test step and each of the
two benchmark invocations. All three captured stderr files are empty.

## Preserved boundaries

- This does not close or weaken #5206's formal promotion requirements.
- No #5139 model/GPU work or Docker invocation/inspection occurred; #5085's
  current restriction was respected.
- No old benchmark result, allocation, branch, or artifact was changed.
- After measurement, two Markdown hard-break whitespace characters were
  removed from `PLAN.md`/`REPORT.md` to make `git diff --check` clean; the H/T/D/C/U
  content and preregistered conditions were not changed. The original plan hash
  remains in the preregistration comment and initial evidence commit history.
