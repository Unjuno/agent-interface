# Current-main Docker/Xvfb MAP01 direct-versus-compiled comparison R03

Source was current main `c7701e08ce13290a9c71aeacaf0af578521f85bb`.
The source tree was mounted read-only into the pinned `linux/amd64` Docker image
`sha256:b473b61c9dda0fab168f4a2118bd1206676dc6913122a3b9193d423426bc0b84`.
The container had no network, a read-only root filesystem and a private Xvfb.

Four fresh matched pairs compared one 600 ms W-forward action on ViZDoom
FreeDoom MAP01: direct guarded X11 dispatch versus the compiled guarded GUI
route. Pair order was counterbalanced. Timing covered the in-path observation,
action, post-release game synchronization and typed task-effect check; startup
and alias preflight were excluded. Each of the eight arms passed all six
preregistered gates: route completion, independent W-down observation during
the call, verified empty terminal release, independent W-up after return,
position delta of at least 0.1, and a successful typed task-effect receipt.
Observed position deltas were 117.211–127.538 X units.

| Pair | Direct ms | Compiled ms | Compiled minus direct | Relative |
|---:|---:|---:|---:|---:|
| 15 | 862.354 | 917.872 | +55.518 | +6.44% |
| 16 | 859.307 | 920.613 | +61.306 | +7.13% |
| 17 | 880.920 | 917.585 | +36.665 | +4.16% |
| 18 | 871.435 | 902.751 | +31.316 | +3.59% |

Mean route latency was 868.504 ms direct and 914.705 ms compiled, a compiled
mean increase of 46.201 ms (+5.32%). The median paired increase was 46.092 ms.
Compiled was slower in all four pairs. This is a small descriptive sample for
one synthetic action on one host; it does not establish model-loop or human
task efficiency, token savings, MAP01 completion, WSLc/Windows transfer, or
broad reliability. The R02 data are not pooled because they used another
source commit.

Focused local verification in the same image passed 44 input-dependency and
core contract tests in normal Python and the same 44 under `python -O`. This
is not a full repository test run.

The task-local raw packet, preregistration, all arm receipts, Docker exit
statuses and hashes are retained at
`private-packets/docker_vizdoom_x11_caller_efficiency_currentmain_20261028_r03/`.
All arm-level results passed. Docker returned status 2 after each trial because
the first shell wrapper was written with CRLF line endings and its final `exit`
argument was parsed as nonnumeric. The runner's own result and receipts were
saved before that wrapper error. No arm was retried; the wrapper defect remains
in the raw record.

## Timing decomposition from retained arm receipts

The raw direct action result and compiled bridge execution receipt expose
`execution.started_ns` and `execution.ended_ns`. Comparing those intervals with
the same arm's outer `caller_path_elapsed_ns` gives this descriptive split:

| Route | Mean full route | Mean bridge execution interval | Mean route time outside that interval |
|---|---:|---:|---:|
| Direct | 868.504 ms | 693.836 ms | 174.668 ms |
| Compiled | 914.705 ms | 695.346 ms | 219.360 ms |

The bridge execution interval differed by only 1.510 ms on average, while the
outside-interval residual differed by 44.692 ms. Both routes ended at bridge
sequence 7 in every pair, so the observed gap is not explained by a higher
sequence count in the compiled route. Each compiled bridge directory retained
37 JSON files versus 18 for direct (19 additional files), reflecting the
compiled plan, graph events, reference/admission, dependency, effect and
terminal receipts. Across the full arm directories, compiled retained about
16.3 KB more per trial on average.

This does not establish that file writes alone caused the latency gap. The
outside-interval residual also includes observations, callbacks, graph
transitions, input-guard work and route bookkeeping; no in-process profiler was
present in R03. A useful next measurement is to instrument these existing
stages separately before changing or batching any custody record. Evidence
records are part of the current safety contract, so performance work must
preserve their failure and replay semantics.
