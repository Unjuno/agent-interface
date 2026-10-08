# Issue #7794 carbon-window scheduler: analytical construction A01

## Disposition

`PASS_METHOD_SCOPED` for a small, deterministic scheduler model only. This is
not the Issue's requested container experiment, realistic-trace result, or an
operational emissions finding. The required OrbStack engine was unavailable:
Docker API image enumeration and image-content access returned HTTP 500 / an
unsupported blob-store operation. No other runtime substitution was made.

## H/T/D/C/U

- **H:** Given finite time slots, fixed job energy, owner-approved feasible
  start windows, and precedence constraints, exhaustive feasible-schedule
  enumeration can identify the minimum-intensity feasible schedule and detect
  any heuristic schedule that is not optimal in this finite model.
- **T:** Enumerate all start-slot assignments for three jobs (durations 1–2
  slots), reject deadline/window/precedence/overlap violations, and compare
  ASAP, latest-feasible, carbon-greedy, and oracle schedules. Include flat,
  inverted, and tied intensity cases, plus an infeasible case.
- **D:** PASS if the enumeration returns a nonempty finite feasible set for
  feasible controls, returns no schedule for an impossible control, chooses
  the minimum listed cost, and the isolated one-job intensity control moves
  from the early to late slot when the intensity profile is reversed.
  Heuristic dead ends and suboptimal schedules are retained as counterexamples.
- **C:** The result can be an artifact of tiny slot discretization, fixed
  energy, known carbon intensity, zero forecast error, and a simplified single
  machine. A clairvoyant oracle is diagnostic, not an implementable policy.
- **U:** No workload realism, measured energy, forecast uncertainty, runtime
  behavior, cancellation/queue interaction, output equivalence in a real
  application, actual emissions, or transfer to agent-interface is tested.

## Reproduction

Run `python3 scheduler_oracle.py`. The script uses only the Python standard
library and writes its JSON report to stdout. The retained `result.json` is the
stdout from that command. An independent post-run assertion checked the four
oracle costs, all four controls, and the number of dead-end dispatcher outputs.

## Result interpretation

The run passed its finite-model gates. It enumerated 12 feasible schedules in
each of four three-job intensity cases. The exhaustive minimum costs were 17
(declining), 20 (flat), 17 (inverted), and 7 (tied). ASAP cost 29 in the
declining case and 8 in the tied case; fixed-order latest-feasible dead-ended
on all four cases, and carbon-greedy dead-ended in the declining case. These
are model counterexamples to these simple dispatchers, not evidence that any
production scheduler behaves this way. Full raw output is in `result.json`.

This analytical construction can answer whether a small scheduler
implementation or heuristic contradicts its own finite model. It cannot
establish Issue #7794's ≥10% operational CO2e criterion. That requires the
separately frozen realistic workload, metered energy allocation, declared
regional/time intensity, and forecast-error replay. A reported model cost is
not an emissions measurement. SCI likewise requires a disclosed boundary and
functional unit and describes operational emissions as energy times regional
intensity; this artifact makes no SCI claim.

Source SHA-256: `c4c39ac012b71d599d4f0101359a8ef720109c31bf18e1279a85d2c9f2096fb1`

Result SHA-256: `0cad5e0f50fb0a3c8ca3b07999177d13614599ba7e448e530f84c33738bf3203`
