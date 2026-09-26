# Result: historical operation result versus current application state

Issue #4366. **PASS_HISTORICAL_RESULT_PROJECTION_SCOPED**.
Source freeze commit:7c937479892296c4abc5746dfea005d248a8b9ec.
Public source readback and authorization comment5832532854 preceded all formal cases.
First-outcome comment5832551159 preceded evidence packaging.

## Measured results

| Per policy | CURRENT_PROJECTION | RECORDED_RESULT |
|---|---:|---:|
| Fresh private cases |12|12|
| Legitimate effect rows |24|24|
| Duplicate effects |0|0|
| Changed-payload conflicts |4|4|
| Delivered replies |46|46|
| Replayed replies |20|20|
| Historical-result mismatches |12|0|
| Wrong numeric values |8|0|
| Same numeric value but wrong version |4|0|

Each response mismatch count includes two prescribed replay probes per affected
case, not independent trials. The control has six affected cases; the candidate
has zero. These are directed contract counterexamples, not population rates.

## Concrete ABA witness

A adds1 to the initial0, committing counter_after1/version1. B adds3, committing
4/version2. C subtracts3, committing1/version3. A's replay through the current
projection returns A/counter_after1/commit_version3. The number agrees, but that
version belongs to C. The recorded-result policy returns A/1/1 and separately
reports current1/version3. Neither policy repeats A's effect.

In OTHER_EFFECT and LOST_REPLY, the control instead returns A/4/2 even though A
committed1/1. This experiment fixes successful effect deduplication and isolates
response projection; #331's current-semantic-validation ordering and #4126's
query/retry transaction test are not repeated.

## Execution and audit

Six immutable batches,24 cases,96 separately exec'd receivers;92 exit0 and4 planned
postcommit/pre-response exits73. Six outer batch exits0. The four missing first
replies remain absent. Eight frozen source hashes unchanged. Raw-only audit1113
checks/errors=[], twelve effective valid copied-evidence mutations rejected
normally (not parser crashes/no-ops). Original audit/controls were separate
processes; same author, not independent human review.

All fresh and new-ID controls work; all altered-payload conflicts refuse. Every
reply authority=false/task_success=null. A successful private counter operation
is not evidence of a real user task. No shared runtime was changed or executed.

Construction:four separately labelled cases/16 receivers,75 and115 audit checks,
eight unit methods. Excluded from formal. No construction/formal process timeout
or unexpected process error occurred. Source-path-portability checking was fixed
before construction. No same-allocation retry/replacement/exclusion/tuning.

## Limits and integration decision

Provided Linux6.18.44 x86_64/glibc2.41,CPython3.13.5,SQLite3.46.1. DELETE journal,
synchronous FULL,timeout0,explicit transactions,separate receiver process for
each request. Docker/OrbStack image identity absent. Clock/frequency uncontrolled;
no timing benchmark or calibrated uncertainty estimate. No GUI/model/provider,
external network experiment,package installation or production input.

This is a known historical-result contract, not a novel exactly-once mechanism.
A legitimately current-state API may return current values: the defect exists
only when they are labelled as the old operation's historical result. Whole
response byte equality is not required. Both policies store the same complete
result; no storage/efficiency advantage was measured. Complete retained identities,
trusted one-scope protocol,cooperating writers and successful commits are assumed.
No power-loss durability,GC,authentication,split brain,arbitrary GUI effect,
model/token/latency or production promotion claim.

For #2789 recovery: expose original_operation_result and current_observation as
separate fields. An idempotent actuator does not by itself establish correct
result provenance. Broader #331/#24/global ROADMAP remain open.

See PLAN.md for full H/T/D/C/U and variable/unit definitions. All actual requests,
replies,SQL logs,initial/per-process/final SQLite files,process receipts,construction,
source,freeze and original audit/control outputs are included in the lossless
archive delivered alongside readable sources. Nonexecuted __pycache__ is excluded.
Temporary mutation directories are reproducible from frozen code and retained
before/after hashes, not themselves retained. Packaging is not a scientific rerun.
