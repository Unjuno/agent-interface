# V39 cancellation cleanup into per-key measurement consumer A04

This additive offline composition asks whether the retained V13 cleanup sample
bracket from PR #7774 can satisfy the strict per-key measurement consumer from
PR #7602 A03 when the original bridge admission context and matching actuation
identity are retained. It performs no GUI, OS input, game, or model operation.

## H / T / D / C / U

- **H:** A unique owner cleanup record can be projected into the A03 consumer's
  `input_release_measurement` schema, paired with the contextualized admission
  by its actuation ID, and independently reconstructed from the raw source.
- **T:** One offline projection of the exact retained PR #7774 A01 raw; run the
  strict A03 candidate consumer and a separate A03 raw-only oracle over the
  result. Mutation controls exercise identity, context, state, timing,
  authority, effect, and output-summary corruption.
- **D:** PASS only if the cleanup identity/context/bracket survives projection,
  the consumer and independent oracle agree, and every corruption is rejected.
- **C:** This composes retained data after the fact. The runtime bridge in A01
  did not emit the projected cancellation measurement.
- **U:** One key and one fake-display cancellation trace. No live OS input,
  GUI/game, model, useful feedback, recovery, or MAP01 progress.

## Result

One frozen offline candidate invocation and the independent audit pass. The
strict consumer accepts the cancellation-cleanup up bracket when joined to the
original bridge admission by its actuation ID and program/step context. Its
single-key fake-display duration bound is 2,578,167–2,588,333 ns
(2.578167–2.588333 ms). This is a sample-bracket bound from fake-display key
state, not an exact physical or game occupancy interval. The original A01
owner raw, bridge events, and result are copied unchanged under `SOURCE/`; no
A01 candidate was rerun.

The raw-only audit returns `PASS_CLEANUP_CONSUMER_COMPOSITION_SCOPED` and
independently reconstructs the projected pair through the frozen A03 oracle.
Four test methods pass in normal and optimized Python, covering 11 corruption
cases. No authority or application effect is claimed. The strict consumer
projection is a post-hoc adapter; A01's runtime bridge did not emit it.

Reproduce from this directory:

```powershell
python build_freeze.py
python -m py_compile candidate.py run_candidate.py audit.py test_a04.py build_freeze.py
python -m unittest -v test_a04.py
python -O -m unittest -v test_a04.py
python run_candidate.py
python audit.py
```

This package is only a downstream data-contract composition. It does not show
that A01's runtime bridge forwards owner cleanup, nor establish physical/game
input, application effect, useful feedback, bounded recovery, threat response,
or MAP01 progress.
