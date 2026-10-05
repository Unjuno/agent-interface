# MAP01 feedback / key-up temporal alignment A01

Status: **scoped source compatibility PASS; live measurement remains untested**.

Base: `e7c916989da30741b00c234efd264067d0899851` (`origin/main` at freeze).

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

## H/T/D/C/U

- **H:** The current source schemas permit a conservative common-clock temporal
  join of independent outcome samples and identity-bound per-key key-up
  receipts without adding a per-key query or publication.
- **T:** Read-only assertions over the eight pinned source files; eight unit
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
```

The next authorized V15 episode can use this join only as a descriptive timing
instrument. It must retain scorer sample windows, missed periods, per-key
release identities/brackets, task conditions, and empty-input verification. A
matched comparison and independent task scoring are still needed for efficacy;
this artifact grants no live allocation.
