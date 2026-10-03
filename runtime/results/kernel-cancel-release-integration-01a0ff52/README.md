# Runtime cancellation release lower bound — #6864

This ordinary engineering repair remembers the first successfully accepted
`begin_execution(now_ns)` and refuses an older release snapshot in `stop()`.
The refusal leaves the lifecycle active and unchanged so a current verified
release can still finish cancellation. Equality is allowed. Invalid first
begins do not create a lower bound; #6853's merged duplicate-begin guard prevents
later calls from overwriting it.

Worker `01a0ff52-93c2-7272-9fbc-2d01287bc6aa`, policy FINAL-v5. Exact source base
`cb13a10dce358649458f5aea00947b8aa43fc5b8` includes the resolved #6852/#6853
single-begin repair. Dedicated branch `fix/kernel-cancel-release-01a0ff52-20261003`.
Original construction in #6868 remains immutable and is not runtime-promotion
approval. This package has a new matrix/source freeze for the actual integration.

## H / T / D / C / U

- H: tying active cancellation evidence to its accepted begin rejects the
  reproduced stale snapshot without weakening valid cancellation.
- T: test-first real kernel regressions; complete kernel suite and core smoke;
  frozen current-main and fixed copies in a 300-row-per-arm matrix; separate
  raw-only oracle; five raw corruption controls and three source mutations.
- D: zero stale post-begin acceptance after repair; equality/later empty verified
  release accepted; refused cancellation/invalid begin leave the operation
  usable; existing duplicate-start and terminal behavior preserved.
- C: a prior empty snapshot does not establish release of a subsequent command.
  This is a same-clock lower-bound consistency check, not a fresh OS observation
  or proof of actual physical release. Authorization without an accepted begin
  retains its original cancellation contract.
- U: sequential trusted API calls and receipt producers only; public field
  mutation, clock comparability, concurrency, backend/OS behavior, effect
  occurrence and live task benefit are not established.

## Executed verification

The six new regression methods first fail with six missing-ContractError
assertions on the exact current-main baseline. The fixed kernel passes 27/27
methods normally and under `-O`; the separate core suite passes 65/65.

The two complete matrices contain 12 declared lifecycle histories and 25 release
cases each. The duplicate-begin history now **expects refusal**, reflecting the
merged #6853 contract while retaining the first request. Baseline still accepts
eight stale cancellations; the fixed copy accepts zero. Independent raw-only
oracle reconstructs both 300-row matrices with no errors. The audit suite passes
six methods: unchanged raw plus five negative corruptions.

Implementation mutation checks execute the real copied lifecycle against the
actual six new runtime regressions. Original passes; removing the bound fails
six assertions; rejecting equality causes three required-success ContractErrors;
remembering rejected begins causes four required-success ContractErrors. All
three mutations are detected with zero unrelated exception types. No tests or
source were changed to make these detections pass.

`FREEZE.json` pins original copied source, candidate/probe/auditor and actual
runtime/test source before matrix execution. `MUTATION_SOURCE_FREEZE.json` adds
the mutation checker and the exact regression copy before mutation checks.
Logs preserve original baseline failure, commands, UTC boundaries and child
exit codes. `.txt` kernel copies and mutation sources execute only through the
explicit temporary-package checks; no workflow is added or altered.

## Reproduce

From repository root with standard-library Python (executed on macOS arm64
CPython 3.14.5):

```bash
P=runtime/results/kernel-cancel-release-integration-01a0ff52
python3 -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python3 -O -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python3 -B "$P/audit.py" baseline "$P/baseline.raw.json"
python3 -B "$P/audit.py" candidate "$P/candidate.raw.json"
python3 -B "$P/check_audit.py" -v
python3 -B "$P/check_mutations.py"
```

`probe.py baseline|candidate` is an ordinary repeatable construction, not a
consumed allocation; write any replay to a new path, preserving retained raw.
The kernel workflow's old explicit `runtime.kernel.test_kernel` command contains
the original 21 methods; local discovery above also runs the new six methods.
Remote CI is not claimed to have exercised the added file merely by turning
green. No formal allocation/container/GPU/model/GUI/input or physical backend ran.

| Field | Japanese meaning | SI unit | Definition / range | Type |
|---|---|---|---|---|
| `execution_started_ns` | 受理された実行開始時刻 | ns = 10^-9 s | 成功した begin の共通時計時刻。未開始は None | optional nonnegative integer |
| `release.observed_ns` | 入力解放を観測した時刻 | ns = 10^-9 s | 同じ時計で記録する。開始と同時刻以上が適格 | nonnegative integer |

Fixture times are authored relationships, not measured nanosecond precision or
latency. The separate begin-to-ExecutionReceipt causality proposal is not adopted;
contracts.py, backend.py, old test_kernel.py and original evidence stay unchanged.
Main delivery requires this runtime proposal's own non-author committee/content
approval and exact combined-tree check, applicable GitHub conditions and one
history-preserving conditional application. #57/#59 remain broader open goals.

Public log correction: private local workspace/home prefixes are replaced in
public traceback text. Exact original bytes are retained privately and read back;
`PUBLICATION.json` records original/published hashes. All test failures, raw
matrices, source and scientific dispositions remain unchanged. The first
published version remains in Git provenance; no history removal is claimed.
