# Missed-period admission-boundary repair

This additive source repair is based on PR #7664 head
`a2f85482c6968f9caa9dcbca017bd452b8a2c3b3`. The original classifier and all
frozen evidence are unchanged. No producer script, game, model, GUI, input,
container, GPU, or formal allocation was run for this repair.

## Defect and minimal policy-faithful change

For accepted intent at 100 and first input at 120, use scorer observations
`(time, kills, missed_periods_before)` of `(110, 0, 0)`, `(120, 0, 1)`, and
`(130, 1, 0)`, with a 100 ns gap bound. The historical classifier selects
baseline 110, skips the 120 observation before inspecting its missed period,
then incorrectly accepts the gain at 130.

`candidate_v2.py` is a versioned copy with one behavioral change: before the
pre-input/admission-time skip, reject a missed period. The existing later
gap check, missed-period check, positive rule and error precedence are kept.
An observation exactly at first input still cannot itself be the post-input
positive sample. A zero-missed observation there continues to be accepted
when a later bounded gain is present. Misses before the selected baseline or
after the first bounded positive observation do not enlarge that interval.

`file_join_v2.py` selects the corrected classifier. `runtime_bundle_v2.py`
selects that corrected file consumer and reuses the unchanged historical
`runtime_bundle_a01_20261005/SOURCE_POLICY.json` and `FREEZE.json` as its default
metadata policy. The renamed modules avoid collisions with historical test
imports. The versioned copies deliberately leave historical source hashes
and saved-record source joins intact.

## Select the corrected entry point

From the repository root, for a co-located directory:

```sh
python research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1/runtime_bundle_v2.py \
  --runtime-dir /path/to/runtime --intent-id recover-1 --max-gap-ns 100
```

For separate JSONL files:

```sh
python research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1/file_join_v2.py \
  --events /path/to/events.jsonl --scorer-samples /path/to/scorer-samples.jsonl \
  --intent-id recover-1 --max-gap-ns 100
```

The second route intentionally retains the historical two-file consumer's
lack of source/summary validation. Use the directory route when those metadata
checks are required. Neither route authenticates episode co-origin or checks
live source contents against the manifest. The default source policy is an
exact historical source inventory, not a claim that arbitrary current-main
runtime outputs match it. This repair does not change those limits.

## Ordinary unit verification

The first direct-function regression against the exact historical candidate
failed: one test, one assertion failure, incorrectly returned
`ADMISSION_BRACKETED_PROGRESS`. The expanded 18-method suite, before the fix,
failed four tests: kill gain, map exit, JSONL consumer, and directory consumer
at the missed-period admission boundary. After the minimal fix, all 18 methods
pass in normal and optimized Python. First RED outputs are preserved in the
private source-repair evidence packet; no historical result was overwritten.

```sh
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1 -p test_boundary.py -v
python -O -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1 -p test_boundary.py -v
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/missed_admission_guard_v1 -p 'test_*.py' -v
python -m unittest discover -s research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2 -p test_audit.py -v
python research/doom/scorer_eventlog_join_t0_v1/saved_record_audit_v2/audit.py
```

Additionally, 16 retained ordinary unit methods were applied to the corrected
functions through `test_compatibility.py`'s test-only module bindings:
3 historical policy tests,
3 file-consumer tests, 1 prior-policy regression, and 9 runtime metadata tests.
All passed. The unchanged saved-history audit's 17 methods and read-only CLI
also passed. This totals 51 distinct focused methods (18 + 16 + 17), with the
18-method optimized run reported separately. Both corrected CLIs reject the
boundary fixture; the directory CLI uses its default policy and freeze.

This is not a full repository test run or a new experiment. The seven saved
runtime RAW cases and historical auditors retain their narrower scope,
clarified in [the package index](../README.md). No live/runtime/causal
conclusion follows from these unit results.
