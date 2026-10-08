# Issue #5734 T0 — fault-free timing coupling

Status: `METHOD_PASS_SCOPED` (synthetic finite method check only).

This directory freezes a small exact-rational event DAG and two independently
implemented exhaustive enumerators. It asks whether bounded, fault-free local
latencies can compose into a response-deadline miss, whether a control with a
loose global deadline remains safe, and whether a missing endpoint oracle is
held rather than guessed. All timing values are authored synthetic integers;
they are not measured from Agent Interface, a model, a GUI, or an operating
system. No probability, safety, causal, runtime, or product claim follows.

## Frozen H/T/D/C/U

- **H:** under a source-supported envelope, locally compliant timing can jointly
  miss an independently defined deadline and evade matched local-boundary-only
  and injected-fault-only suites. T0 cannot test source support or those
  empirical baselines; it tests the finite composition mechanism only.
- **T0:** enumerate the frozen DAG in `fixtures.json`; include a loose-deadline
  uncoupled control, a coupled near-boundary case, and missing-oracle HOLD.
- **D:** `METHOD_PASS_SCOPED` iff all local bounds and clock relations hold,
  the loose-deadline control has no misses, the coupled case has an exact
  all-local-pass miss, the independent enumerator agrees, and missing endpoints
  return `HOLD_NO_ORACLE`.
- **C:** a single global bound or existing system-level constraints may already
  expose the same schedule, making a coupling ledger unnecessary. No comparison
  against #5327/#5330 is performed here.
- **U:** DAG, intervals, deadline, and outcome labels are synthetic and
  analyst-authored; integer ticks merely permit exact rational arithmetic.
  Correlation, clock drift, real harm, effective intervention, calibrated
  distributions, source-supported ranges, and baseline fairness are untested.

## Frozen experiment

Each of five sequential functions has an inclusive local duration interval
`[1,2]` synthetic ticks: capture, deliver, decide, guard, and actuate. The
exogenous cue occurs at tick 0. Durations use one synthetic monotonic clock;
the response endpoint is the sum at effective-action completion. Enumerate all
`2^5 = 32` schedules. The control deadline is 11 ticks; the coupled deadline is
8 ticks. Thus no individual function exceeds its local maximum, but composed
latency can cross the coupled global deadline. These values were fixed before
running either enumerator and carry no empirical calibration.

Run from repository root:

```sh
python3 research/analysis/functional_coupling_5734_t0_v1/analyze.py
python3 research/analysis/functional_coupling_5734_t0_v1/audit_independent.py
```

The first enumerator emits canonical JSON to stdout. The second recomputes the
space using a separate direct-product implementation and checks the expected
counts/outcomes. Commands, raw outputs, hashes, and limitations are in
`RESULT.md` and `SHA256SUMS`.
