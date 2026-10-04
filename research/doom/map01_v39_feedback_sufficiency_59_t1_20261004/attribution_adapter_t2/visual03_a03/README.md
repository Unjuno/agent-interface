# Visual03 adapter replay A03

This offline replay uses the exact visual03 V16/V39 record merged by PR #7571:
761 independent scorer samples, one positive kill-count event, and all 19
input admissions plus 19 release transitions. Raw slices, source hashes, and
the adapter pins are in this directory.

The pinned #7561 adapter originally returned `HOLD_INCOMPLETE_RELEASE_BATCH`.
The same program id is reused across sequential steps, each with its own
size-1 release batch. The old integrity key grouped those steps together and
mistook the repeated position 0 for an incomplete batch. The repaired key
includes `release_batch_step`.

The replay then returns `SOURCE_ROWS_JOINED` and one `TEMPORALLY_UNIQUE`
possible-intent envelope for the kill-count event. The candidate intent is
`41a11010ac2d4543bfb8d4f2b4bb8f83`; the scorer interval is
`[28348735736, 28398091723]` ns. `causal_attribution` remains
`NOT_ESTABLISHED`. The release boundary in this V16 data is an owner XSync
receipt with `physical_verification_authoritative=false`; this result does not
establish physical key-up timing or causal input effect.

Run from the T2 adapter directory:

```powershell
python -B visual03_a03/run_replay.py
python -B visual03_a03/audit.py
python -B -m unittest -v test_visual03_adapter_composition.py
```

This replays retained rows only. It uses no live input, model call, GUI, or
formal allocation.
