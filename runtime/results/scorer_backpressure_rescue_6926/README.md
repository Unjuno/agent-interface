# Native scorer pipe backpressure archive rescue

Original PR #6926, remote `research/scorer-pipe-backpressure-59-20261003-01a0ff33`,
exact source `c5360b1a80ce0af28c013cc8bdfcfed5ad1e60c9`. Preserve all 93 packet
files unchanged, including original insufficient optimized aggregate qualification,
separate V2 validation, actual native streams and private/public receipt mappings.

Independent archive checks cover 92 manifest entries and all original Git bytes,
six source witnesses against their historical Git snapshots, and the explicit
raw-only verifier normally and with optimization: all 20 retained native stream
pairs, 13 frozen files and eight copied-raw corruption refusals.

Historical finite Windows construction: 12 pre-drain FINISH observations, four
blocked-direct censored rows and four capacity-one refusals. All 16 non-overflow
rows eventually process FINISH and persist after parent drain. Source termination
with pending spool bytes is not final persistence; a missing command in 200 ms
does not prove an infinite hang. Neither current verification nor historical
construction adopts this custom sink into production or preempts arbitrary
nonreturning callbacks.

No child/deck/adapter/producer, old allocation, native input, model or GUI is run.
Local checks authenticate retained evidence, not fresh Windows/POSIX/live effect,
latency/efficiency, task progress or resolution of Issues #57/#59. Old review and
private capture chronology qualifications do not become new integration votes.

```sh
python3 -m unittest discover -s runtime/results/scorer_backpressure_rescue_6926 -p 'test_*.py' -v
```
