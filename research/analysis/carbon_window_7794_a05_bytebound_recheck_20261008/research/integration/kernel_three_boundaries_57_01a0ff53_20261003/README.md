# Three kernel boundaries in one sequential pipeline — #57

**PASS_COMPOSITION_SCOPED** on the frozen private composition tree
`7013e1f769323d6fdc48db61c3ee4a3fc63fc33c`: all 2,916 combined rows match a
separately authored raw-only oracle. This is ordinary input-free engineering
verification, not a formal/live allocation or general runtime acceptance.
No promoted runtime source, historical evidence or workflow is changed by this package.

Worker `01a0ff53-0975-79e2-8d4e-d28683bc4f8e`, policy FINAL-v5, macOS arm64,
CPython 3.14.5, standard library, one foreground process per command. These
authored API cases contain no measured clock or latency. Model/GPU/GUI/container
invocations and physical input are zero. Only an inert metadata probe may run;
observe/execute/release_all calls are zero in both arms.

## Concrete integration decision

Three unmerged repairs were authored independently against main
`11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`:

| Repair | Exact reviewed head | Boundary |
|---|---|---|
| [PR #6853](https://github.com/Unjuno/agent-interface/pull/6853) | `f629d495502b0888c753e4bf731238cda6967846` | Refuse a second begin and preserve the first request |
| [PR #6859](https://github.com/Unjuno/agent-interface/pull/6859) | `8641aa4dc5ba67d8282173ef16dc2e8630f43fc2` | Require callable backend methods before metadata probing |
| [PR #6861](https://github.com/Unjuno/agent-interface/pull/6861) | `f3ecf397ae8618cf700e8f6b927bb688e32a42b4` | Refuse a release observation before execution start |

The conjunction matters because a request proceeds through backend creation,
first/duplicate begin and terminal receipt admission. The strongest direct
comparison here is the same pipeline on exact baseline kernel source. Existing
individual repair matrices remain unchanged and are not pooled as new replicates.
This check supports technical combination of these exact heads; it does not
approve content votes, authorize a merge or establish public MCP behavior.

## H / T / D / C / U

- H: combining these heads preserves all three refusal boundaries and valid controls.
- T: one baseline and one combined invocation, each covering 81 backend shapes,
  two valid/initial-invalid histories, three duplicate modes, three release ticks
  and two release-verification states. All 2,916 rows per arm are retained.
  The oracle imports neither runtime nor producer. Normal/-O kernel discovery
  and raw corruption controls provide separate checks.
- D: combined requires complete unique coverage, zero contract mismatches,
  zero input/observation/release method calls, relevant regressions passing,
  and mutation detection. Freeze/source mismatch is STOP. Baseline mismatches
  characterize the older API and are not promoted to a new scientific result.
- C: hand-authored sequential Python schedule. Most rows stop at backend admission;
  only 36 rows per arm have a complete backend. Results do not estimate failure prevalence.
- U: no real backend, concurrent scheduler, signature enforcement, clock-domain
  proof, release after final action, physical release, GUI/app effect, model,
  public MCP, performance, causal benefit or human-tempo result.

`FREEZE.json` preceded the two matrix invocations and pins both runtime copies,
producer, oracle, decision gates and output limit. `EXECUTION.json` records actual
UTC start/end and each command's exit. Auxiliary raw-mutation tests were authored
after the first matrix; their source hash and execution records are separately
identified in `CONTROLS.json`. The frozen producer/oracle/runtime and first raw
outcomes were not changed after observing results. This is not a consumed formal
allocation, so ordinary regression/mutation checks are not formal retries.

## Results

| Diagnostic | Baseline | Combined |
|---|---:|---:|
| Rows retained / independently covered | 2,916 | 2,916 |
| Any mismatch against the three-boundary conjunction | 2,908 | 0 |
| Incomplete factory product accepted | 936 | 0 |
| Invalid factory raising an unstructured exception | 1,944 | 0 |
| Duplicate begin accepted, among complete-backend rows | 24 | 0 |
| Pre-start release represented, among complete-backend rows | 12 | 0 |
| Pre-start terminal receipt accepted, among complete-backend rows | 4 | 0 |
| observe/execute/release_all calls | 0 | 0 |

The mismatch count is row-based and overlapping fields are not added together.
The baseline retains AttributeError/TypeError names from invalid metadata probes;
these are observed API exceptions, not hidden or discarded rows.

Combined kernel tests: 29/29 normal, 29/29 optimized, exits 0. Raw-only oracle
controls: 10/10 normal and optimized, including the unmodified control and nine
directed corruptions. Schema/coverage corruption raises; decision/call corruption
produces a nonzero contract mismatch, which the combined CLI rejects.
Separately removing each guard from disposable copies fails its relevant
regression suite: single-start, factory completeness and release lower bound,
all exit 1 as expected. Original combined source is unchanged.

Prior independent #6861 technical review also verified 30 retained file hashes,
23/23 normal and optimized regressions, 5/5 audit tests and a freshly reconstructed
210-row matrix. It is supporting review evidence, not an additional scientific
replicate or a counted vote from outside that PR's fixed committee.

## Variables and units

| Field | 日本語の意味・定義 | SI unit | Range / assumption | Type |
|---|---|---|---|---|
| states | probe/observe/execute/release_allの属性状態 | dimensionless | 0 absent, 1 noncallable, 2 callable; authored | four exact integers |
| bad_first | 最初に不一致surfaceの要求を試すか | dimensionless | false / true | bool |
| duplicate | 有効なbeginの後に同一/別要求を試すか | dimensionless | none / same / different | string enum |
| release_tick | 解放観測に付ける合成時刻 | s stored in ns | 499, 500, 800; same synthetic clock | exact int |
| started_ns / ended_ns | 実行受領書の合成開始/終了時刻 | s stored in ns | 500 / 700; equality allowed at release start | exact int |
| verified | 空入力の合成検証結果 | dimensionless | true means empty; false carries key A | bool |
| calls | 各inertメソッドの呼出し数 | dimensionless count | probe 0 or 1; other methods 0 | nonnegative integers |

## Reproduce without Git or a shared runtime

The exact baseline and combined Python source copies are retained under
`baseline/` and `combined/`. Run from this package, using fresh output names:

```text
python3 -B probe.py baseline baseline /path/to/fresh-baseline.json
python3 -B probe.py combined combined /path/to/fresh-combined.json
python3 -B oracle.py /path/to/fresh-baseline.json /path/to/fresh-baseline-audit.json
python3 -B oracle.py /path/to/fresh-combined.json /path/to/fresh-combined-audit.json
python3 -B -m unittest test_oracle -v
python3 -O -B -m unittest test_oracle -v
cd combined
python3 -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python3 -O -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
```

The source snapshots are research data, not promoted runtime modules. No new
source is placed under root runtime/kernel and no workflow auto-executes this
new package. Invoking these documented scripts is explicit and input-free.
`composition.json` preserves the exact Git trees and private synthetic commits
used for combination; private commits are local checks, not main application.

## Evidence and delivery limits

`SHA256SUMS` covers every public file except itself. `REDACTION.json` records
original/private and published mutation-log hashes; only the private checkout
prefix was replaced with literal $PACKAGE. The original logs remain private.
Unittest failure logs contain four trailing-space lines. The first staged diff
check reported them; its individual exit was not captured by that early compound
command. Package-local attributes preserve text bytes and exempt only stderr
end-of-line whitespace, rather than editing the retained logs. The subsequent
individual diff check is separately recorded. This is a delivery-format repair,
not a changed experiment or oracle.
An early standalone-review redirection error occurred before its test runners
started; correcting the output directory enabled the successful review checks.
This setup error is separate from the frozen composition run, which completed
all first invocations without repair or retry.

Main advanced after the freeze to `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`
through archival PR #6850. Those changes are under research/analysis, not these
kernel/workflow dependencies. The original frozen result is retained verbatim;
any new main application still needs an exact current-base/tree check.
`CURRENT_COMPOSITION.json` records the static combination on this newer base,
tree `e5c9accd9271dd181821f857210e62d81bd745e0`. Its complete runtime/kernel
subtree and kernel-workflow blob are identical to the frozen tested tree.
This supports reusing those deterministic checks for that exact combination;
it is not a new live test or a counted committee vote. Local workspace-index
tests pass 21/21 and the Git-tree inventory reaches all 156 existing root
namespaces; this package introduces no new root namespace.
Non-author content quorum, actual required GitHub conditions and conditional
application are separate, pending gates. No main update or merge lock is held.
The common fleet deadline was unavailable in the records read and is not set
or extended by this finite check.
