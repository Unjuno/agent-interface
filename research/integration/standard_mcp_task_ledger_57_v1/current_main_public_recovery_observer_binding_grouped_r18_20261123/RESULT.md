# R18 — grouped recovery and caller regressions

## Frozen question and conditions

Do three R16-failing recovery/public-caller tests pass together in one process when each mode uses a unique temporary root? Conditions and source hashes were frozen before execution. The same ordered three-test group ran once normally and once under `-O`, without retry.

## Results

Both process invocations exited 0 and reported `Ran 3 tests ... OK`:

| Mode | Result | Duration |
|---|---:|---:|
| Normal | 3/3 passed | 4.038 s |
| `-O` | 3/3 passed | 4.035 s |

The group covered late completion recovery, unknown completion-observer recovery, and the public compiled-caller exact-result/task-oracle composition. Logs and exit receipts are retained under `raw/`; both modes had separate TEMP/TMP/TMPDIR roots.

## Interpretation and limits

The selected cases pass both separately (R17) and when grouped in one process (R18). This narrows the R16 failure condition toward the full-suite host/run context or cumulative workload, but does not identify the cause or validate the full 63-test module. R16 remains failed. The result is Fake/local test evidence only: no native task effect, live GUI/input, reliability estimate, efficiency comparison, MAP01, or Research Preview acceptance.

## Next step

Keep R16 as the failed broad regression result. Avoid another unchanged full-module rerun. Resume the project gate with a finite standard-caller recovery/effect trial after its independent scorer, release/horizon evidence, attempt accounting and source pins are frozen; preserve UNKNOWN separately from task effect and recovery release.
