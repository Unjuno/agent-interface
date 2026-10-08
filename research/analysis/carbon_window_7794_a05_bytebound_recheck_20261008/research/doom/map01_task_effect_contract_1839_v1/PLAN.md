# MAP01 task-effect instrumentation contract — frozen offline rung

Allocation: `MAP01-TASK-EFFECT-CONTRACT-1839-20260928-01`\
Intake main: `2ac5a00b9879c48f0ecf304c1d3ff01fe4c18ad8`\
Branch: `research/map01-task-effect-instrumentation-contract-1839-20260928`

## H — hypothesis

A minimal descriptive contract can represent physical actuation, public state
feedback, and independently scored plan-bound task effects as three distinct
evidence roles. It will accept one exact-lineage synthetic positive while
refusing weak, unbound, mistimed, cross-clock, duplicated, or scorer-tainted
records, without granting input or task authority.

## T — frozen finite experiment

- Candidate: `contract.py`; structurally separate reference implementation:
  `oracle.py`; raw-only auditor: `audit.py` imports neither.
- Run one fixed 13-record corpus via `run.py`: three role-positive controls
  (bound task effect, state-only, effect without actuation) and ten hostile
  controls (viewport, HUD, terminal, run total, pre-down effect, foreign plan,
  foreign actuation, non-independent scorer, controller scorer, unrelated clock).
- Candidate and oracle classify each row. Auditor independently reconstructs
  physical lineage and effect eligibility directly from retained raw records.
- The prior v38/v39 records are not counted as positive rows; their documented
  limitation is a separate missing-endpoint negative control.
- No model/provider, GUI/X11/ViZDoom, input, network, GPU, or container.
- Exactly one deterministic runner and one raw-only audit; no retries or
  replacement cases.

## D — gates

`PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED` requires 13/13 candidate/oracle/expected
agreement, all negative controls fail closed, one positive task effect binds
only after the physical-down upper bound on the attested common monotonic axis,
state feedback remains non-authoritative, audit errors=0, and authority flags
remain false. Any role promotion or candidate/oracle disagreement is FAIL.

## C / U — limits

All rows are synthetic. Temporal order is not causal proof. This does not
measure actual OS input, exact key-up duration, clock comparability in a live
multi-process run, model/task performance, or MAP01 efficacy. A PASS only
establishes this finite event-contract boundary and does not authorize a live
allocation.
