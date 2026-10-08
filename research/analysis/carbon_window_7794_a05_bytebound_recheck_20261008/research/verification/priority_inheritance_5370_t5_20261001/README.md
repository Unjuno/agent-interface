# Issue #5370 T5 — waiter deadline ordering under bounded inheritance

This is an additive, deterministic host-CPU experiment. It advances Issue #5370's T0–T4 toy scheduler ladder without changing earlier artifacts.

## H / T / D / C / U

- **H:** With the same authenticated waiters and the same bounded owner inheritance, selecting blocked verifiers by earliest absolute freshness deadline rather than arrival order reduces stale/late completions when arrival order conflicts with deadlines, without permitting a late or unauthenticated admission.
- **T:** Replay a fixed one-resource workload: low-priority holder `L` owns `R` for two service ticks; medium work `M` has five units; one-tick verifiers `H1` and `H2` also need `R`. In the discriminator, `H1` arrives at tick 0 with deadline 5 and `H2` at tick 1 with deadline 3. Compare no-inheritance/FIFO, two-tick bounded inheritance/FIFO, and the same inheritance with EDF waiter selection. Add equal-deadline and unauthenticated-priority controls. A separate standard-library-only auditor reads the raw JSON and does not import the runner.
- **D:** `PASS_WAITER_DEADLINE_ORDER_SCOPED` only if the deadline-conflict FIFO inherited policy completes `H1` and stale-abstains `H2`, EDF completes both by their deadlines, the no-inheritance baseline stale-abstains both, equal-deadline ordering is stable and FIFO-compatible, the forged urgency is rejected without changing inherited priority, inherited owner work stays within two ticks, and the independent audit has zero errors. Any late admission, unauthenticated elevation, or budget overrun is FAIL; missing/changed frozen inputs or incomplete raw/audit is STOP.
- **C:** In the primary comparison, the workload, arrivals, priorities, owner critical-section length, medium work, admission deadline rule, and inheritance budget are identical; only waiter order (FIFO vs EDF) changes. The no-inheritance baseline is reported separately as the inversion control.
- **U:** One synthetic discrete scheduler, one deterministic trace family, and one Python 3.11.9 host. This is not evidence about a live scheduler, hidden wait-for edges, stochastic latency, task quality, or production fairness. No GPU or Docker run is included; shared local container/GPU work was active during this rung.

## Execution boundary

Research package path: `research/verification/priority_inheritance_5370_t5_20261001/`.

Construction tests in this task workspace: `python work/test_5370_priority_inheritance_t5.py -v` (completed 4/4 before freeze). After checkout, the byte-identical test is under `src/test_5370_priority_inheritance_t5.py` beside the runner.

Frozen formal runner in this task workspace: one invocation of `python work/5370-priority-inheritance-t5-20261001.py`. After checkout, invoke the byte-identical runner at `src/5370-priority-inheritance-t5-20261001.py`.

Independent raw-only audit in this task workspace: one separate invocation of `python work/audit_5370_priority_inheritance_t5.py` with the exact frozen runner JSON on stdin. After checkout, use `src/audit_5370_priority_inheritance_t5.py`. No rerun, tuning, or seed changes under this allocation.

The source/input SHA-256 digests, base main, expected cases, and commands are in `FREEZE.json`.
