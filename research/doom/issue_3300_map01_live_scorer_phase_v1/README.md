# #3453 — live MAP01 scorer phase/span allocation

This additive successor measures the unchanged current-main
`session_map01_v13.py::_coherent_progress_sample` getter sequence against a
continuously advancing ViZDoom/Freedoom MAP01 `ASYNC_SPECTATOR` session. It does
not reuse or relabel the `basic.cfg` runs under #3300 or #3456, and does not
modify gameplay policy, retry count, shared runtime, or prior evidence.

## H/T/D/C/U

- **H:** Under a live 35 Hz MAP01 clock, unequal getter spans, phase, and gaps
  can change the observed outcome of the existing three-attempt coherence
  predicate relative to #1461's equal-span ideal geometry.
- **T:** Freeze ten integer-nanosecond phase targets (including the exact n=3
  #1461 boundary and its ±1 ns / ±1 μs neighbors), three strata, and four
  episode-disjoint repetitions per cell. A no-button `ASYNC_SPECTATOR` driver
  advances the engine; a separate phase probe brackets observed tic edges; the
  unchanged production scorer is invoked exactly once per episode and retains
  its existing three internal coherence attempts. The CPU-load
  stratum applies the frozen 50%-duty local load; delayed-read adds 20 ms after
  the requested target. No model, network, OS input, desktop, or task-control
  component is present.
- **D:** Retain every case, including setup/API/cleanup failures, source/WAD/
  container identities, exact getter calls and timestamps, tic-edge brackets,
  call spans, retry gaps, scorer return/error, and cleanup. The standard-library
  auditor independently rebuilds each attempt, decision, phase interval, and
  per-stratum fraction of predicate invocations whose three internal attempts
  are all incoherent. The formal output path is
  `results/formal-01/raw.jsonl`; its exclusive invocation guard prevents a
  second collection at that path.
- **C:** Any scoped PASS is limited to this pinned public Freedoom 2 v0.13.0
  MAP01 fixture, ViZDoom 1.2.3, 35 Hz target, and frozen schedule. The scheduled
  row fraction is not a natural phase-probability estimate. No gameplay,
  model-utility, OS-capture, hard-real-time, universal retry-bound, or human
  tempo claim follows.
- **U:** Whether the deployed scorer's observed phase/span/gap distribution
  changes its three-attempt coherence rate beyond this controlled fixture and
  schedule remains unknown. Any policy change needs a separate successor.

## Frozen allocation design

The nominal period is `28,571,429 ns`. The target phases are
`0, 7,142,857, 14,285,714, 19,046,619, 19,047,618, 19,047,619,
19,047,620, 19,048,619, 21,428,571, 28,571,428 ns`. Each target is run four
times in each of `idle`, `cpu_load`, and `delayed_read`: 120 rows total, each
with a distinct game session and seed. #1461's n=3 boundary is 19,047,619 ns.

Requested target offsets are not treated as actual phase. The probe records
the preceding and detecting monotonic getter brackets; the independent audit
uses those bounds and each actual scorer `tic_before` timestamp to reconstruct
an interval for every attempt's phase. It reports the interval uncertainty.
If a tic edge is skipped or cannot be matched, that attempt's phase remains
unidentified and the decision is HOLD, not imputed from the requested sleep.

## Construction and formal execution

Construction runs use a different output path and are never included in the
120 formal rows. Build the frozen arm64 image from the repo root; the WAD is
the official Freedoom v0.13.0 release asset, mounted read-only at runtime. The
formal command is run once with `--network none` after `FREEZE.json` records the
image ID and hashes. Preserve stdout/stderr and the exact Docker invocation.
Run `audit.py` only after collection; it does not call or import the scorer.
Excluded construction evidence is audited with `--mode construction`, which
reports `PASS_CONSTRUCTION_ONLY` and never requires the 120-row formal guard.
The one formal run uses `--mode formal --freeze FREEZE.json` after collection.

`FREEZE.json` is the pre-collection freeze. `RESULT.md`, raw rows, independent
audit, environment manifest, invocation metadata, and SHA-256 list are appended
only after the one formal run. A setup stop or HOLD is retained as-is; no
rerun, replacement, threshold change, or post-result schedule tuning.

The prior 1.2.3 formal candidate stopped before freeze or collection; see
`results/formal-01/STOP.md`. Follow-up 1.3.0 construction runs are reconciled in
`CLOCK_WITNESS_RECONCILIATION.md`: passive getter snapshots stayed stale for
2 s, while one post-interval `advance_action(1)` exposed a +71/+72 tic
catch-up. The unchanged scorer returned first-attempt coherent from that stale
snapshot in 3/3 fresh sessions. This is useful construction evidence, but not
a reconstructed live phase witness or formal result. Formal rows remain
0/120 and construction evidence remains excluded.

A separate, read-only `get_server_state()` probe was added after the passive
snapshot discrepancy: 155/157/155 calls across three new 2 s sessions showed
`ServerState.tic == get_episode_time() == get_state().tic == 3` throughout.
The server-state API does not act as an independent live-clock witness in this
fixture; see the appended run-18/19 setup/API diagnostics and valid run-20 data
in `CLOCK_WITNESS_RECONCILIATION.md`.

Run 21 then compared all three tic views before and after a single endpoint
`advance_action(1, True)`: the passive values remained 3, then the call exposed
77/75/75 in all three APIs. This associates the visible snapshot catch-up with
the action boundary but does not locate live tic edges during the wait.

Run 22 removed the display server entirely and repeated the passive no-action
observation in three fresh headless sessions: 150/154/160 reads over 2 s, with
`get_episode_time()`, `get_state().tic`, and `get_server_state().tic` fixed at
1 throughout. The unchanged scorer returned its first coherent sample at tic 1
in all three. Raw output and a byte-identical host/container audit are retained
under `results/construction-clock-22/`. This is excluded construction evidence,
not a formal result; disposition remains `HOLD_NO_INDEPENDENT_LIVE_TIC` and
formal rows remain 0/120.

Run 23 tested the explicit `new_episode()` startup call against the implicit
post-`init()` state in six matched headless sessions (three per condition).
Across 2 s and 155–169 reads each, all three tic views stayed at 1 in every
session; the scorer returned coherent at tic 1 in 6/6. Explicit
`new_episode()` returned in about 82 ms but did not change `is_new_episode()`
or unlock passive tic progression. Audit disposition:
`HOLD_NEW_EPISODE_DID_NOT_UNLOCK_PASSIVE_TIC`. This rejects only the narrow
startup-call explanation, not the possibility of a paused engine; it remains
excluded construction evidence and formal rows remain 0/120.

Run 26 freshly reproduced the issue runner's separate-thread empty-button
`advance_action(1)` driver with official Freedoom 0.13.0 and full image/WAD
identity: 3/3 phase intervals reconstructed, `PASS_CONSTRUCTION_ONLY`, zero
audit errors. The measured rates were 33.25/34.54/36.92 Hz across the three
strata. Because this requires repeated episode-advancement calls—and the issue
review explicitly disallows that as a substitute for passive clock progress—it
is an intervention-only instrumentation check, not a formal result.

Run 27 tested one empty `set_action([0]*9)` assignment after explicit episode
start against no assignment (six matched headless sessions, three per arm).
All three exposed tic views remained at 1 across 2 s in all 6/6 sessions; the
scorer returned coherent at tic 1 and cleanup completed. No `advance_action`
or `make_action` call occurred. The matched independent audit returned
`HOLD_EMPTY_SET_ACTION_DID_NOT_UNLOCK_PASSIVE_TIC` with zero errors. This
excludes one narrow startup-action explanation; it does not prove the game
engine itself is paused. Evidence is retained under
`results/construction-clock-27/` and remains excluded from formal rows.

Run 28 compared `available_buttons=[]` with nine registered-but-unused buttons
in three matched pairs. All three tic views stayed at 1 in 6/6 sessions over
2 s; scorer and cleanup succeeded, and no set/advance/make-action call was
made. The byte-identical host/container audit reports
`HOLD_BUTTON_INVENTORY_DID_NOT_UNLOCK_PASSIVE_TIC` with zero errors. This tests
the exact empty-button setup condition but still does not produce a live phase
witness; see `results/construction-clock-28/`.

Run 29 compared hidden MAP01 `ASYNC_SPECTATOR` and `ASYNC_PLAYER` in three
matched pairs, with explicit episode start and no action-advancement calls.
Both modes remained fixed at each session's starting tic (first pair 2, later
pairs 1), all three API views agreed, and scorer/cleanup succeeded in 6/6.
Audit: `HOLD_BOTH_ASYNC_MODES_PASSIVE_TICS_STATIC`, zero errors. This narrows
the mode-specific hypothesis but does not change the formal issue's declared
mode or resolve the missing passive phase witness. See
`results/construction-clock-29/`.

Runs 41–42 tested a new source-instrumented timing path. Against pinned
ViZDoom 1.3.0 source, a minimal patch samples `CLOCK_MONOTONIC` at the first
operation of a helper called at `VIZ_Tic` entry, before debug-log formatting,
then appends `{pid, monotonic_ns, gametic, vizTime}`. Two independent
three-session allocations returned the exact scorer and closed 3/3; corrected
audits bracketed all 48 getter starts between successive engine clock samples.
Construction-only getter phase positions and microsecond-scale spans are now
observable without host/container clock conversion. This does not bound
helper-call or clock-read latency, and the per-tic append perturbs scheduling.
An append-only erratum narrows the initial overstrong “tic-entry witness” audit
label. Formal phase accuracy and allocation remain unresolved (0/120); details,
raw data, build recipe and failed/corrected audit history are retained under
`results/construction-clock-41/` and `results/construction-clock-42/`.

Run43 replaces the per-tic append syscall with an in-memory source trace flushed
once at engine exit, while sampling `CLOCK_MONOTONIC` directly as the first C
statement in `VIZ_Tic`. A fresh three-session Docker allocation completed 3/3
and the audit correlated all 24 getter starts. This reduces one instrumentation
cost but leaves compiler-prologue/clock-read uncertainty and scheduling
perturbation unbounded; it is not formal phase evidence. See
`results/construction-clock-43/`; formal rows remain 0/120.

Run44 tested whether a kernel uprobe could remove that remaining userspace
entry-latency uncertainty. The exact read-only probe in the pinned arm64 image
found `perf_event_paranoid=2`, no mounted tracefs/debugfs or uprobe event
control, and no `CAP_SYS_ADMIN`/`CAP_PERFMON`. No game was launched and no
privilege escalation was attempted. Disposition:
`STOP_KERNEL_UPROBE_UNAVAILABLE_IN_DEFAULT_CONTAINER`—an environment stop,
not a scientific result. Formal rows remain 0/120. Probe and captured output
hashes are in `results/construction-clock-44/invocation.txt`.

Run45 then tested the Issue's actual passive async-clock/scorer compatibility
question in OrbStack Docker, with no `advance_action`/`make_action`/`set_action`.
In three fresh instrumented MAP01 sessions, the engine's contiguous internal
`VIZ_Tic` trace ran at median 34.012/35.260/35.433 Hz, but 118–119 passive
`get_episode_time()` reads per session stayed at tic 1. The unchanged exact
scorer returned after one coherent attempt in all 3/3 and its two tic getters
also returned 1. A corrected second run retained all eight scorer getter calls
per session; the final entry sample preceded scorer start by 14.54–19.99 ms,
so phase remains unidentified. Independent audit:
`PASS_CONSTRUCTION_ONLY_ENGINE_PROGRESS_API_TIC_STALE`, zero errors. This is
direct construction evidence of an internal-engine/public-API clock mismatch,
not the requested phase/span distribution. Formal allocation remains 0/120.
See `results/construction-clock-45/` for the two preserved 3-session runs,
import STOPs, raw traces, audit, Docker logs, invocation, hashes and H/T/D/C/U.

Run46 then tested the exact action boundary as a construction intervention.
Across three new sessions, passive API/scorer tic remained 1; one empty
`advance_action(1)` made the public API and exact scorer jump to tic 55 in 3/3.
The independent internal trace ended at tic 58 and measured 34.724–35.669 Hz.
Audit: `PASS_CONSTRUCTION_ONLY_ACTION_BOUNDARY_CATCHUP`, zero errors. This
locates the stale-snapshot refresh at the action boundary in this fixture, but
the action is not the no-intervention formal condition and provides no passive
scorer phase distribution. See `results/construction-clock-46/`; formal rows
remain 0/120.

Run47 tested the narrower zero-tic refresh hypothesis. `advance_action(0)`
returned quickly (0.093–0.386 ms) but left public API and exact scorer tic at 1
in 3/3 sessions despite 57 contiguous internal engine tic entries in each.
Independent audit: `HOLD_ZERO_TIC_ACTION_DID_NOT_REFRESH_SNAPSHOT`, zero errors.
This rejects only the zero-tic refresh route; formal rows remain 0/120. See
`results/construction-clock-47/` for H/T/D/C/U, Docker invocation, raw/audit,
logs and hashes.

Run48 tested an AArch64 `CNTVCT_EL0` measurement path: the pinned engine's
`VIZ_Tic()` object begins with `MRS CNTVCT_EL0`, and exact scorer getters were
bracketed by the same hardware counter. Three sessions yielded 24/24 fully
bracketed getters and 34.62–35.10 Hz engine entry rates while public API tic
stayed at 1. Audit: `PASS_CONSTRUCTION_ONLY_CNTVCT_PHASE_INTERVALS`, zero
errors. But this VM's counter quantum is 41.67 ns and getter intervals are
0.375–41.333 μs; uninstrumented scheduling effects also remain unbounded. Thus
the ±1 ns boundary neighbors cannot be distinguished and formal remains 0/120.
See `results/construction-clock-48/` for disassembly, complete invocation,
failures, raw phase bounds, audit and hashes.

Run49 compared the run48 per-tic CNTVCT/clock/ring-buffer build against the
same pinned ViZDoom 1.3.0 source rebuilt without that patch. Four alternating
fresh-session pairs (8 × 6 s passive ASYNC_SPECTATOR sessions) completed in
OrbStack Docker. Independent audit: `PASS_CONSTRUCTION_ONLY_CPU_COST_COMPARISON`,
8 rows, zero errors. Paired process-CPU/wall-time differences were positive in
2/4 pairs and negative in 2/4; median difference −0.000110 (fractional CPU),
so this small construction sample detects no consistent CPU-cost increase.
One control session's public API tic moved from 1 to 2 while all instrumented
sessions stayed at 1; the uninstrumented engine's tic rate was not independently
observable. This is not evidence that scheduling perturbation is absent, nor a
phase witness. Formal allocation remains 0/120. Full paired raw rows, both
images, build/failed-attempt logs, invocation, audit and hashes are under
`results/construction-clock-49/`.
