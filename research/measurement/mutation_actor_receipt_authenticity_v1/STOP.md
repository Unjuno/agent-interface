# Formal stop — #1263

Disposition: **STOPPED_OUTER_EXECUTION_TIMEOUT_NO_SCIENTIFIC_RESULT**.

- Source-first freeze completed before formal.
- Exactly one formal invocation was launched.
- The container tool hit its 45 s execution ceiling before the frozen program emitted its aggregate JSON.
- `FORMAL_STDOUT.json` exists but is exactly 0 bytes.
- No exit-code artifact was written.
- Post-stop process inspection found no surviving `experiment.py` process.
- Same-allocation rerun/replacement/tuning: 0.
- Construction controls remain excluded and are not promoted to scientific evidence.

A fresh successor may change only outer execution granularity / batching while keeping receipt semantics, canonicalization, keys, seed, total corpus, gates, and first-outcome discipline unchanged.
