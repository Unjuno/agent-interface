# R17 — isolated observer and caller regressions

## Frozen question and conditions

Do representative R16-failing and candidate-specific tests pass when each is run in a fresh Python process with a unique temporary directory? Conditions and source hashes were frozen in `conditions.json` before execution. Three exact tests were each run once normally and once under `-O`; all six commands completed without retry.

## Results

All six invocations report `Ran 1 test ... OK` and have exit code 0:

| Test | Normal | `-O` |
|---|---:|---:|
| `test_cancel_before_admission_is_retained_and_prevents_producer_start` (R16 failure representative) | PASS | PASS |
| `test_queued_supervised_observation_keeps_server_bound_fake` (candidate binding) | PASS | PASS |
| `test_public_compiled_caller_joins_exact_result_query_and_task_oracle` (R16 failure representative / R15 composition) | PASS | PASS |

Each process had a distinct TEMP/TMP/TMPDIR. Full command output and exit receipts are retained under `raw/`; `SHA256SUMS.txt` binds all files.

## Interpretation and limits

The isolated successes show that the selected R16 failures do not reproduce in these fresh, one-test processes. This supports an execution-context/interference explanation for at least these cases, but does not identify the cause of every R16 failure or establish that the full module passes. The R16 optimized run overlapped several unrelated `scripts/ci/task_queue.py` processes on the host; that concurrency is a plausible confound, not proven causation. Keep R16 recorded as failed and avoid promoting these three cases into a reliability estimate.

The observer-binding test is synthetic Fake evidence. No live GUI, OS input, provider/model, independent task effect, MAP01, efficiency, or repeated-recovery cohort was exercised.

## Next step

Retain the per-test process isolation and unique temp roots for narrow verification. Diagnose remaining full-suite cleanup and worker interference from exact tracebacks before selecting another broad run. Then return to the finite public standard-caller recovery/effect gate; do not widen isolated feature experiments.
