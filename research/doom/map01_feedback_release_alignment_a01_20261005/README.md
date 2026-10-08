# MAP01 feedback / key-up temporal alignment A01

Status: **scoped source compatibility PASS; one retained live-construction trace aligned posthoc**.

Analysis base: `40f15b8b04fbdc33327fd18d52250930fb03aee1` (`origin/main` at
analysis freeze). This base contains the retained run and all nine exact source
snapshots referenced by its `FREEZE.json` and runtime `sources.json`. The run
itself is historical; its source identities are verified against its snapshots,
not silently equated with current source files.

## Question and finding

Can the V15 independent useful-outcome observations be placed on the same time
axis as the current per-key release receipts without inserting work between
individual key-up operations?

The retained source contract says yes, for temporal comparison only:

- V15 scorer samples and V3/V4 owner release brackets use
  `time.perf_counter_ns()` in the same process.
- Each scorer read has an outer `sample_started_ns` / `sample_finished_ns`
  window and an internally tic-coherent progress payload. V15 schedules at
  35 Hz; missed periods and actual intervals are retained, so 28.6 ms is a
  nominal period, not a guaranteed onset bound.
- Each owner receipt nests the XTest KeyRelease/XSync interval inside the
  caller's release-call bracket. The release batch performs one owner-state
  sample after the last key-up and only then publishes its buffered rows.
- `ProgressClock` labels kill-count increase and map exit as positive useful
  events; those events remain scorer-only and are not controller-visible.

`alignment.py` conservatively bounds an observed counter transition by the
previous negative sample's start and the first positive sample's finish. It
compares that interval with the owner KeyRelease/XSync bracket and returns an
unresolved result when intervals overlap. The tests also reject a row that
claims physical verification authority.

## Retained V16 trace application

The read-only analyzer pins and rereads the already-retained
`59-4d74-current-visual-construction-03-20261004` files at the same base. Across
761 scorer samples and 19 key-release rows, the first useful positive event is
the sole `KILL_COUNT_INCREASE`, from sample sequence 392 to 393. Its conservative
outer sample-window onset is `[28.331791183, 28.402303781] s` in the run clock.
For plan `plan-1-primary-0-1`, the Space KeyRelease/XSync bracket is
`[28.018728291, 28.019034822] s`; the later `a` input is acknowledged at
`28.215940081 s` and its key-up/XSync bracket starts at `28.575882021 s`.
Therefore the sampled kill transition lies wholly after Space XSync and wholly
inside the later `a` hold, with a descriptive delay of **312.756–383.575 ms**
from Space XSync return to the conservative kill-onset interval.

The retained scorer summary records 198 missed nominal periods, a 75.163 ms
p95 sample interval, and a 147.362 ms maximum interval. The specific transition's
70.513 ms conservative read-window interval is therefore reported directly;
the nominal 35 Hz schedule is not used as a guaranteed latency bound.

This is useful timing evidence from one retained construction trajectory, but
it does not assign the kill causally to the recent Space pulse: a delayed effect
from that or earlier fire remains possible. The episode had no MAP01 exit, no
death, and no observed policy invalidation. Existing saved-interval audit
disposition remains `HOLD_CAUSAL_INPUT_ATTRIBUTION; HOLD_POST_INVALIDATION_RECOVERY`.
`RETAINED_V16_RESULT.json` carries hashes for the exact raw inputs. The separate
raw-only audit script independently recomputes the interval and identity joins.

## H/T/D/C/U

- **H:** The current source schemas permit a conservative common-clock temporal
  join of independent outcome samples and identity-bound per-key key-up
  receipts without adding a per-key query or publication.
- **T:** Read-only assertions over the eight current-source files and nine
  run-pinned snapshots; eight unit
  cases for sample-window bounds, invalid intervals, release receipt scope, and
  temporal ordering.
- **D:** PASS only for same-process timestamp compatibility and the stated
  publication ordering. FAIL if any clock differs, sample execution windows are
  absent, or a per-key operation inserts an owner state sample/publication.
- **C:** A common monotonic clock does not make the event causal or physically
  authoritative. OS scheduling, Doom sampling time within the coherent call,
  and gaps between samples remain uncertain.
- **U:** No V15 live episode or new X11/game/model call was run. Sampling cadence
  overruns can widen the interval. Kill count/map exit are the currently typed
  useful outcomes; damage, ammunition, navigation, and player survival onset
  need separately validated measurements. XSync does not prove physical key
  state or application consumption.

## Reproduction

From repository root:

```powershell
python -m unittest discover -s research/doom/map01_feedback_release_alignment_a01_20261005 -p test_alignment.py -v
python research/doom/map01_feedback_release_alignment_a01_20261005/audit_source_contract.py
python research/doom/map01_feedback_release_alignment_a01_20261005/analyze_retained_v16_trace.py
python research/doom/map01_feedback_release_alignment_a01_20261005/audit_retained_v16_trace.py
```

The next authorized V15 episode can use this join only as a descriptive timing
instrument. It must retain scorer sample windows, missed periods, per-key
release identities/brackets, task conditions, and empty-input verification. A
matched comparison and independent task scoring are still needed for efficacy;
this artifact grants no live allocation.
