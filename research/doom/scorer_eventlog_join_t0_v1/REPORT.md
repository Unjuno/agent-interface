# MAP01 scorer/event-log join T0

## H / T / D / C / U

**H.** The current v15 event and scorer records have a common guest monotonic clock and an intent ID, so an offline policy can join accepted intent, first input admission, and independent useful progress. The baseline must be the freshest scorer sample after acceptance and before first input; an older baseline can treat progress already seen before input as a later gain.

**T.** Seven deterministic fixtures were frozen against the field shapes emitted by ExecutorV13 (`accepted_ns`), input-owner-v12 (`id`, `admitted_ns`), ScorerFileSink v1 (`sample_started_ns`, `sample_finished_ns`, `missed_periods_before`, `payload.sample_ns`), and ProgressClock v2 (`kill_count`, `map_exit`). The limit is a 100 ns baseline-to-positive observation gap. Cases cover a valid join, progress seen only before first input, a stale-baseline trap, missing baseline, a missed scorer period, malformed sample timing, and duplicate acceptance identity.

**D.** The frozen source commit is `d6a024437dae00198f6b1aea7b397e3e0d03a0cf` (base `decefbd53240cdac21633e0d3e66c7e3bec76722`). The runner produced seven rows; local audit passed with one admission-bracketed row and six co-occurrence rejections; the three focused tests passed. In particular, the stale-baseline case rejects because the latest pre-input sample already includes the kill. The prior T0 policy selects the first sample after acceptance, so it can misclassify that history if a later sample merely repeats the elevated count.

The frozen OrbStack gate **STOPPED before candidate launch**. `docker pull --platform linux/arm64 python:3.12-slim` failed because the containerd content-store blob could not be opened (`operation not supported`); `docker image inspect` failed with the same store error. No identical container retry was made. The candidate, independent audit, and focused tests then ran locally with Python 3.12.13 on macOS arm64 as a separately labeled fallback; this does not turn the frozen container gate into PASS. See `STOP.json`.

**C.** The retained PASS is local deterministic policy construction using synthetic single-clock inputs. No game, model, live input, GPU, Docker execution, WSLc, or formal allocation occurred. The Docker gate is STOP. The result demonstrates that the source fields can be joined by ID and timestamp under the constructed cases; it does not demonstrate actual episode file parsing, scorer timing under load, recovery efficacy, or MAP01 completion.

**U.** `ADMISSION_BRACKETED_PROGRESS` means a useful counter transition was observed after the first input, compared with the freshest available state after accepted intent and before that input, within the configured bound and without a missed scheduler period in that interval. It does not locate the underlying game event or prove the recovery caused it. A live run still needs the current-main V39 lineage, complete per-key admission/up/release receipts, independent scorer files, and an authorized matched bounded-recovery allocation.

## Reproduction

At the frozen source commit, run:

```sh
python research/doom/scorer_eventlog_join_t0_v1/run.py
python research/doom/scorer_eventlog_join_t0_v1/audit.py
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1 -v
```

The candidate/auditor/test commands above were executed locally after the container STOP. `raw.json`, `audit.json`, `STOP.json`, and `SHA256SUMS.txt` preserve the outcome and limits.
