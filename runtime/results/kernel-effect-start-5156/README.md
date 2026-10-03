# Recorded-start lower bound for typed effect evidence

Ordinary engineering repair for [#5215](https://github.com/Unjuno/agent-interface/issues/5215):
`RequestLifecycle.record_effect` now refuses `observed_ns < execution.started_ns`
before changing effect or stage. Its two-line guard requires the existing
comparable-clock assumption. Equality, observations during execution and late
receipt delivery remain representable. It does not prove a final-action
postcondition, genuine clock provenance or application success.

- [Report](REPORT.md): exact scope, original failures, later checks and limitations.
- [Original repair plan](PLAN.md) and [first setup qualifications](SETUP_NOTES.md).
- [TDD freeze](TDD_FREEZE.json): the first baseline's source hashes were recorded
  after execution; they are not presented as prospective baseline proof.
- [Prospective matrix plan](MATRIX_PLAN.md), [35-input freeze](MATRIX_FREEZE.json),
  [180-row raw](raw.json) and [separate raw-only audit](audit.json).
- [Source ledger](SOURCE.json), inert exact source snapshots under `retained/`,
  [capture projections](CAPTURES.json) and [file manifest](MANIFEST.json).

Only `runtime/kernel/lifecycle.py`, its new six-method regression module and
kernel explanation change outside this additive evidence directory. Snapshot
files end in `.py.txt`; no `__init__.py` or `test_*.py` is added here. The two
ordinary programs require explicit invocation and never operate physical input.
The new active regression is picked up by the existing kernel discovery command.

The first six-method baseline exited1 with eleven expected missing-guard
assertion failures. Repair-focused six methods and kernel49 methods in normal
and optimized Python each exited0. C01 then ran once per source-comparison/raw
audit, both exit0: baseline admitted12 pre-start matching rows, candidate0,
with18 valid matching rows and60 identity refusals preserved; all8 effective
copied-raw controls refused. These are author-executed ordinary engineering
checks, separate from genuine nonauthor content/combination review.

Historical #5216/#5225/#5229 evidence and first HOLD dispositions remain unchanged.
This does not adopt their disputed effect-after-end or action-end lease cutoff.
The public MCP path does not currently consume this kernel. No backend/OS input,
GUI, model/provider, container/GPU, task or performance result is claimed.
