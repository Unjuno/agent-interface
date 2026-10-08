# A02 construction preview — formal source-freeze STOP

## Disposition

`STOP_PREFORMAL_SOURCE_UNFROZEN`. The A02 formal allocation was **not** started: candidate/auditor formal counts are 0/0. One full-size construction driver ran in a separate scratch copy before a source/input freeze manifest existed. Its output is preserved under `construction_pre_freeze/`; it must not be treated as a formal Issue result, and the same seed set is not retried.

## Construction-only observations

- Candidate driver: 432 episode/cost rows, 63,424 streamed ticks.
- Independent raw-only replay: all 432 rows and 63,424 ticks reconstructed with no base errors; all four effective mutation controls rejected.
- Informative cohort: the 10% median-cost gate versus both baselines held in four of six checkpoint/replay-cost cells, and failed in the other two.
- Signal-independent cohort: the sequential gate did not disable adaptation by tick 48 in every case.
- Reversed-association cohort: not every policy/task completed within the 240-wall-tick cap; this makes the frozen all-cohort exact-completion requirement fail in this construction.

These observations are engineering feedback about this unfreezed construction, not a formal PASS/FAIL or evidence for a production checkpoint policy. The A02 working sources, fixtures and the temporary-copy executed candidate/audit bytes are retained so the provenance gap is visible. No outcome-conditioned threshold or horizon repair is made in A02.

## Hashes of temporary-copy construction evidence

The actual candidate/policy bytes and generated inputs/outputs are in `construction_pre_freeze/`. Their SHA-256 values are in `CONSTRUCTION.json`; the temporary run used current main `41df296f3ce4d03c801c998d38f6e537e64a83ab`, host CPython 3.14.5, no container, and no GUI/model/user/external effect. Its raw audit was exploratory only. The planned formal paths remain absent.

## Continuation boundary

Any continuation must use a new allocation and additive result path, fresh train/validation/held-out seeds, freeze every source and input hash before candidate execution, and a prospectively justified finite horizon/calibration-abstention design. Preserve this STOP unchanged. Do not reuse A02 as a successful formal run or quietly replace its source/output.
