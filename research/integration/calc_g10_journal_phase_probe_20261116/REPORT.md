# Reproducible append-phase probe — 2026-11-16

## Question

Does canonical JSON/hash work or durable `fsync` dominate the retained 38-record journal append measured in the Fake X public-caller comparison?

## Conditions and method

On Windows 10 / CPython 3.11.9 at main commit `628e275748c7a1143a753a1bc459bdd2a687a1c0`, replayed the exact 38 payloads from the retained journal whose SHA-256 is `6f042128467e027b1412862a0d74b83a7e3c8fef462f9c925aaa7693c1f69260` (46,796 bytes). Three separate output journals were generated using the real `ReceiptJournal.append`; the implementation and `os.fsync` were not disabled. Instrumentation timed canonical serialization, stream writes, flush, and fsync. After each run, the journal was rescanned and every reference/payload was read back and compared.

## Result

Across three repeats, median total append time was 1.228 s. Median component time: fsync 1.215 s (98.9% of total), canonical JSON 3.82 ms, stream write 0.092 ms, flush 1.40 ms; 38 fsync calls per replay. All three 38-record outputs passed complete reference/payload readback.

This confirms fsync dominates this isolated append replay, not that it causes the whole 3.635 s core-time difference in the prior two-pair caller contrast. The replay is a separate run and does not profile observation, process RPC, effect checks, or other caller work. The durability contract was retained; no runtime change was made.

## Reproduction

`python research/integration/calc_g10_journal_phase_probe_20261116/run_probe.py`

Run from repository root with repository root on `PYTHONPATH` (PowerShell: `$env:PYTHONPATH = (Get-Location).Path`). Raw per-record and component timings are in `raw/RESULT.json`; generated journals are `raw/repeat-1/` through `raw/repeat-3/`.

## Next diagnostic boundary

Profile the remaining public-call spans against the same retained method conditions, especially observation serialization/RPC and effect evaluation, before considering any storage-policy change. Any proposal must preserve the current fsync-backed custody contract or prove an equivalent durability boundary.
