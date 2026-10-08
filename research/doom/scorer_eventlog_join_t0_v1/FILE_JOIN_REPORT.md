# MAP01 scorer JSONL consumer follow-up

## H / T / D / C / U

**H.** The admission-bracket policy should consume the runtime's separate `events.jsonl` and `scorer-samples.jsonl` artifacts directly, while failing closed when either file is missing or malformed.

**T.** Four retained JSONL file fixtures use the event and scorer receipt fields emitted by the current-main MAP01 composition: a valid join, a kill already observed before first input, a missing scorer file, and malformed event JSON. The acceptance gate uses a 100 ns baseline-to-positive bound and the freshest post-acceptance, pre-input sample.

**D.** The frozen runner and raw-only auditor passed all four cases. The direct CLI returned `ADMISSION_BRACKETED_PROGRESS` for the valid fixture. The complete focused suite passed 7/7, including the exact-source regression against merged #7471. The original seven-case T0 and exact-source follow-up hash manifests also verify. The source freeze is commit `61d7ad0893e5dc9cc9d1a7a865d960d946cbdcc3` on base main `b47d4d0b053f6e7d88c37e24be81777aa28feb6a`; see `file_join_raw.json`, `file_join_audit.json`, and `FILE_JOIN_SHA256SUMS.txt`.

**C.** This is local deterministic JSONL-consumer construction using synthetic runtime-shaped files on Python 3.12.13/macOS arm64. It is not a run over actual MAP01 output. No game, model, live input, GPU, Docker container, WSLc, or live allocation ran. The earlier OrbStack content-store STOP remains unresolved; no pull retry was made.

**U.** The CLI accepts two file paths separately and does not validate `sources.json` or `scorer-summary.json`; callers must select files from the same episode and clock domain. This construction does not establish source authenticity, scorer timing under load, exact effect time, causality, recovery efficacy, or MAP01 completion. The coordinator hold in #61 still precludes the live experiment.

## Reproduction

```sh
python research/doom/scorer_eventlog_join_t0_v1/file_join_run.py
python research/doom/scorer_eventlog_join_t0_v1/file_join_audit.py
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1 -v
python research/doom/scorer_eventlog_join_t0_v1/file_join.py \
  --events research/doom/scorer_eventlog_join_t0_v1/file_join_fixtures/valid/events.jsonl \
  --scorer-samples research/doom/scorer_eventlog_join_t0_v1/file_join_fixtures/valid/scorer-samples.jsonl \
  --intent-id recover-1 --max-gap-ns 100
```
