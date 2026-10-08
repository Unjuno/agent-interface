# Kernel release observation lower bound — #6855

Bounded engineering repair under #57, worker `01a0ff34-0b3d-7921-846a-6044960fcf76`, policy FINAL-v5.
Base: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
Only `runtime/kernel/contracts.py` and the new `test_release_epoch.py` change executable kernel behavior/tests; kernel README adds the contract and test command.
No lifecycle.py/test_kernel.py edit, backend operation, shared runtime, container, GPU, input, model or formal allocation was used.

## Problem and change

A terminal execution receipt starting at 500 accepted a verified empty snapshot observed at 0, 100 or 499.
The lifecycle accepted that old snapshot as the new execution's terminal release.
The constructor now raises ContractError if its release observation predates its execution start.
Equality is allowed because the timestamps cannot establish order within one clock tick.
Release observations after ended_ns remain representable: this change does not conflate action completion with later release observation/delivery.

## H / T / D / C / U

- H: the constructor can refuse pre-start release evidence while preserving same-tick and later observations.
- T: retain test-first failures, apply the two-line guard, run kernel contracts plus five regressions, enumerate 210 integer input rows before/after, and independently reconstruct raw rows and coverage.
- D: all pre-start observations refused; equality and later observations accepted as representations; unverified snapshots still cannot complete the lifecycle. Any mismatch fails verification.
- C: hold identity, action count, input emptiness and fixture constant; vary start/end/observation time and verified flag. A raw-only auditor uses ordered events and imports neither kernel nor producer. Mutation checks operate on copies.
- U: common comparable clock assumed; no clock-domain token exists in this contract. This lower bound does not establish release after the final action, physical input state, freshness of standalone stop receipts, temporal effect/lease validity, OS safety, app effects, reliability, performance or human tempo.

The original #5215/#5225/#5229 probe/audit source, raw, allocation and HOLD/ambiguity remain unchanged.
This is an ordinary repair/regression matrix, not a retry, independent formal allocation, or new scientific PASS.
RequestLifecycle is not the public MCP execution path. No public-path benefit is claimed.

## Variables and units

These values are authored integer test inputs; no real clock was measured.

| Field | 日本語の意味・定義 | SI unit | Range / assumption | Type |
|---|---|---|---|---|
| started_ns | 実行受領書が記録する開始時刻 | s, stored in ns (10^-9 s) | 0..4, common synthetic clock | exact int |
| ended_ns | 実行受領書が記録する終了時刻 | s, stored in ns | started_ns..4 | exact int |
| observed_ns | 入力解放受領書が記録する観測時刻 | s, stored in ns | 0..6, same clock | exact int |
| verified | 合成の空入力観測が検証済みか | dimensionless | false / true; no physical witness | bool |
| representation_accepted | 実行受領書の生成が受理されたか | dimensionless | false / true | bool |
| terminal_accepted | lifecycleが実行終了証拠を受理したか | dimensionless | false / true | bool |

## Retained results

- Original kernel: 18/18 passed before repair.
- Test-first baseline: 23 test methods, four failed subcases from two methods (three stale verified snapshots and one stale unverified snapshot); runner exit 1, preserved in before-tests.log.
- Fixed kernel: 23/23 passed normally and with Python -O, runner exits 0.
- Baseline raw: 210 rows, 40 pre-start snapshots represented, including 20 accepted terminal receipts.
- Fixed raw: 210 rows, zero pre-start representation/terminal acceptances. Both raw-only audits reconstruct all rows.
- Auditor: 5/5 test methods passed, rejecting 12 directed corruptions (missing/duplicate rows, decision/type errors, missing/extra/null rows, revision and hash syntax errors).
- Implementation mutation copies: missing guard, reversed guard and equality refusal all fail the regression suite with exit 1. These are expected mutation failures, not failed fixed-source checks.
- Compile and git diff --check: exit 0.

Exact commands, observed UTC start/end and runner exits for final verification/mutations are in verification.json.
Earlier baseline commands have preserved outputs and explicit exit status; their start/end timestamps were not collected and are not reconstructed.
Windows host CPython 3.11.9 was used; platform/version strings are in each matrix.
git diff --check's checkout line-ending warning is retained; it is not a test failure.

## Evidence and reproduction

probe.py generates constructor/lifecycle observations with exclusive-create output.
audit.py reads raw only, requires exact schema/types and all 210 unique cases, and reports the retained baseline gap separately from audit reconstruction success.
test_audit.py changes copies only.
SHA256SUMS pins every public evidence file except itself. provenance.json records base Git blobs/canonical Git-byte hashes and the tested checkout hashes.
Baseline contracts checkout used CRLF (raw matrix source SHA-256 f3287cb43ac7f557db7d35b754109432a1dcc9952a389784978963d28260ef9c).
The canonical baseline Git bytes hash to cd37284c15d01f2fde446d53ba161b4bc6224dfb0137324101f3d2eef8884ef8.
The initial fixed tested checkout mixes CRLF/LF and hashes to 8e1d6e2706545e41d871b7a5660472929c63ed3eae397ec1130c510c66f3bfb6.
Exact initial baseline/fixed source bytes are retained as tested-baseline-contracts.txt and tested-fixed-contracts.txt; these are nonexecuting source snapshots.
Final publication normalizes the changed kernel files to canonical LF. Contracts SHA-256 is 884331ccfc5d4694bf88c1086c09ec435963848c44d76c591c27fe38b3b42969.
The canonical source separately passes 23/23 normally and with -O, plus the same ordinary 210-row matrix with zero gaps and an independent audit; see canonical-verification.json and fixed-canonical.json.
These representations are distinguished; checkout hashes are not asserted to equal historical Git-byte hashes.

From repository root:

```text
python -m unittest runtime.kernel.test_kernel runtime.kernel.test_release_epoch -v
python -O -m unittest runtime.kernel.test_kernel runtime.kernel.test_release_epoch -v
python -m unittest discover -s runtime/results/kernel-release-epoch-01a0ff34 -p test_audit.py -v
python -m compileall -q runtime/kernel runtime/results/kernel-release-epoch-01a0ff34
git diff --check
```

For a fresh ordinary matrix replay, choose unused paths; never overwrite the retained baseline/fixed outputs:

```text
python runtime/results/kernel-release-epoch-01a0ff34/probe.py fixed replay-fixed.json
python runtime/results/kernel-release-epoch-01a0ff34/audit.py replay-fixed.json replay-fixed-audit.json
```

The unchanged hosted kernel workflow runs only test_kernel; it does not run the new focused module.
The local focused suite is explicit above. Hosted checks, nonauthor review, current-main composition and conditional application are separate integration gates.
The existing two inspected retained kernel-adapter fixtures use release observation 20 and start 10, compatible with the new bound; they were inspected, not rerun as experiments.

## Publication and next step

Absolute checkout/user prefixes in public failure/mutation logs are redacted; original output is retained privately with hashes in provenance.json/redaction.json.
Only additive publication records are included. No raw outcomes were changed.
This candidate needs FINAL-v5 nonauthor consensus and exact current-main integration evidence before merge.
No merge, broad safety claim or resolution of #5215/#5229 is asserted by this package.
