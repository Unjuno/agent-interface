# Issue #5352 T10 — fail closed after observed bound breach

## Why this rung

Issue #5352 T9 reports that a local envelope admitted under declared disturbance
bound 3 had 6,261 violations in 15,625 traces when the actual alphabet extended
to 4. T9 explicitly leaves bound calibration or a separate fail-closed response
as the next question. T10 tests only the latter after the out-of-bound evidence
has become observable. It does not alter or rerun T0–T9.

## H / T / D / C / U

- **H:** A generation- and sequence-bound fail-closed gate can prevent any
  additional local-continuation permit after an observed out-of-bound or
  critical event, without suppressing in-bound continuation or silently
  re-arming after stale evidence.
- **T:** Freeze bound `B=3`. Exhaustively enumerate every disturbance sequence
  of lengths 1–4 over `{0,1,2,3,4}` (780 traces). Compare an unguarded static
  continuation arm with a candidate that checks each currently observed sample
  before permitting the next local step. Add eight literal edge controls:
  current critical events at the first and later sample, generation change,
  sequence gap, duplicate sequence, exact bound 3, first breach 4, and a low
  sample after a breach. Preserve the complete ordered raw rows.
- **D:** `PASS_BOUND_BREACH_STOP_SCOPED` only if an independent raw-only auditor
  exactly reconstructs all 788 records; all 440 traces containing a value 4
  enter `YIELD_REQUIRED`; the static arm permits 730 later steps across 355
  traces after the first breach while the candidate permits zero; all
  in-bound sequences remain identical to static continuation; and all eight
  controls match their frozen expected outcomes. Any post-breach candidate
  permit, missed current critical override, automatic stale/gap rebase, or
  in-bound suppression is FAIL. Freeze/source/raw/audit mismatch is STOP.
- **C:** Paired policies receive identical traces and horizon. The only policy
  difference is the candidate's current evidence/critical/bound gate before
  the next local permit. The threshold and enumeration are fixed before the
  formal runner; no tuning follows its outcome.
- **U:** Deterministic synthetic CPU fixture only. It does not calibrate `B`,
  prevent the first out-of-bound event, establish that a disturbance is
  observable before harm, validate a runtime, grant action authority, or show
  task quality, latency, GPU/model, GUI, MAP01, or human-tempo benefit.

## Frozen execution boundary

- Allocation: `planner-hysteresis-5352-t10-bound-breach-20261001-01`
- Platform: local Windows x64, CPython 3.11.9, standard library only.
- Construction: `py -3.11 -B -m unittest -v test_runner`; AST parse of the
  runner, auditor, and tests. These construction checks passed 8/8 before
  freeze.
- Formal: invoke the frozen runner exactly once; if and only if it exits 0,
  invoke the frozen raw-only auditor exactly once in a separate process.
- No retries, threshold tuning, Docker/OrbStack, LM Studio/model, CUDA/GPU,
  network, GUI, or effectful input. The deterministic finite run has no need
  for the GPU; a separate active task is preparing the shared RTX 3080 lane.
- Raw outcome, even if failing, is immutable. A STOP or FAIL is retained as
  such; no replacement run is authorized by this plan.

