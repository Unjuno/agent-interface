# Issue #5734 T0-v2 — explicit topology contrast

Disposition: `METHOD_PASS_SCOPED` for the synthetic graph mechanics only.
This is a separately frozen exploratory successor after the v1 design review;
it does not upgrade or overwrite v1. The preregistration/correction is recorded
on Issue #5734 before the v2 commands were run.

## H/T/D/C/U

- **H:** source-supported ordinary timing ranges can compose into a deadline
  miss invisible to matched local-boundary-only and injected-fault-only suites.
  This synthetic rung cannot test source support, real harm, or comparator
  fairness.
- **T0-v2:** enumerate all 32 assignments of five `[1,2]` synthetic durations
  for three frozen graphs: parallel functions (deadline 2), five-stage chain
  (deadline 8), and chain with missing oracle. Use exact rational/integer ticks
  and an independent graph enumerator.
- **D:** scoped method PASS iff parallel control has 0 misses, chain has an
  all-local-valid deadline miss, the independent audit agrees, and missing
  oracle holds.
- **C:** a direct composed bound or #5327/#5330 systems-level methods may expose
  the same timing case without a coupling ledger. No such baseline comparison
  or equal-budget search is run.
- **U:** topology, ranges, deadline, cue, and one-clock assumption are
  analyst-authored synthetic values; no distribution, correlation, effect,
  harm, intervention, or source-supported timing envelope is measured.

## Frozen graph and method

All functions start from a cue at tick 0; each has inclusive duration 1 or 2.
For `parallel_control`, no function depends on another and completion is the
maximum end time (deadline 2). For `coupled_chain`, dependencies are
`capture → deliver → decide → guard → actuate` (deadline 8). The missing-oracle
case uses the chain but has no deadline. Enumerate every duration assignment
(2^5 = 32) separately for each case. No sampling or probability interpretation.

Run from repository root:

```sh
python3 research/analysis/functional_coupling_5734_t0_v2/analyze.py
python3 research/analysis/functional_coupling_5734_t0_v2/audit_independent.py
```

Full command results, scope, and hashes are retained in `RESULT.md` and
`SHA256SUMS`.
