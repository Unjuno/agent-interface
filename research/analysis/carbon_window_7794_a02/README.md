# Issue #7794 T0 carbon-window replay A02

## Disposition

`PASS_METHOD_SCOPED` for deterministic scheduling mechanics across the frozen
finite synthetic cases. The experiment was run with local Python on macOS, not
inside Docker/OrbStack or WSLc. At execution, OrbStack Docker Engine 29.4.0
reported 98 stopped containers; image enumeration failed with a blob-store
`operation not supported` error. No existing container or image was used.

This does **not** satisfy Issue #7794's separate ≥10% criterion on a
preregistered realistic trace and does not establish actual or avoided CO2e.
No owner-approved real deferrable workload trace, energy meter, carbon-factor
allocation boundary, or measured scheduler/rework overhead was available.
Accordingly, the emissions effect remains `HOLD_ACCOUNTING`; synthetic energy
and intensity values below test only scheduling logic.

## H/T/D/C/U

- **H:** With explicit release/deadline/freshness windows, fixed output hashes,
  precedence, and time-varying declared intensity inputs, exhaustive finite
  scheduling can separate ASAP, latest-feasible, intensity-minimizing,
  risk-aware, and clairvoyant diagnostic schedules while preserving hard
  constraints. Only eligible optional jobs may move; mandatory jobs stay at
  their ASAP placement.
- **T:** Freeze [`frozen_cases.json`](frozen_cases.json); enumerate all
  non-preemptive one-machine schedules. ASAP is canonical-order serial
  earliest placement; latest-feasible maximizes the sum of start slots, with
  canonical-order tie breaking. Replay these baselines,
  forecast-carbon minimum, a fixed mean-plus-half-range risk score, and
  clairvoyant per-scenario minima. Include variable, no-flex, flat, inverted,
  forecast-shift/reversal, long-job, precedence, cancellation, infeasible, and
  mandatory-job controls. Run a separate recursive auditor that reconstructs
  feasibility, costs, output hashes, mandatory placements, and oracle minima.
- **D:** `PASS_METHOD_SCOPED` if the independent auditor verifies every returned
  schedule and objective, all fixed output hashes, no mandatory delay, all
  feasible controls, and explicit rejection of the infeasible window.
  `HOLD_ACCOUNTING` remains the disposition for any real operational-CO2e
  reduction claim until a realistic eligible trace, energy meter, declared
  region/time factor, and allocation boundary exist. No synthetic result may
  satisfy the Issue's ≥10% realistic-trace gate.
- **C:** A one-machine, small-slot, fixed-energy model can exaggerate the
  available flexibility. Forecast weights and the risk score are declared toy
  choices. Real host contention, idle/wakeup cost, errors, rework, data expiry,
  or shared-load attribution could eliminate or reverse any estimated gain.
- **U:** Only nine hand-authored synthetic cases; no empirical workload
  representativeness, actual meter, live forecast, operational scheduler,
  remote-provider energy, marginal grid emissions, or output recomputation is
  evaluated. Output equivalence is a frozen identity invariant in this model,
  not a real application execution result.

## Reproduction and audit

From this directory:

```sh
python3 run_t0.py > result.json
python3 audit_t0.py
```

The solver uses finite Cartesian enumeration. The independent auditor uses a
separate recursive enumeration implementation and recomputes schedules,
deadlines, freshness, overlap, precedence, costs, scenario risk, output hashes,
mandatory placement, and clairvoyant minima. `result.json` is the exact retained
solver output. The audit reported `PASS (9 cases)`.

## Result

The enumerated feasible schedule counts were: variable intensity 105; no-flex
1; flat 12; inverted 12; long-job 20; precedence 10; cancellation 5;
infeasible-window 0; mandatory-guard 12. The infeasible case returned
`FAIL_CONSTRAINT` with no schedule. Every other case returned feasible policies
and passed independent reconstruction.

On the synthetic variable-intensity case, ASAP cost was 44, forecast-only
carbon-minimum cost 10, and risk-aware forecast cost 26 (declared robust score
28.5). Under the declared forecast-reversal scenario, their costs were 21, 53,
and 33 respectively. This shows the mechanism's forecast sensitivity in this
fixture; it is not a projected percentage reduction or empirical emissions
outcome. The no-flex
case had one feasible schedule and no scheduling choice. Flat intensity kept
equal cost across placements, and the inverted profile favored earlier
placement. In the mandatory guard, all non-ASAP policies preserved the
mandatory job's ASAP start.

## Source identities

- `frozen_cases.json`: `afa9d6f50183125a1188f0c018fe41f1e2c7b142ceaddba76f6d278718af4be2`
- `run_t0.py`: `3949d580fe14527a694ae0ef393aa27eb5e8fe25b1ac234fe83a8299eff7e841`
- `audit_t0.py`: `3650d826eaa15572c24d0a1bac2c5071dd860f2166ef0c52831bc895d6b505e4`
- `result.json`: `e7d10e427f1d9d32f304936bb9a9bbe118896aebdca0de070aa8a596a3b21d23`
