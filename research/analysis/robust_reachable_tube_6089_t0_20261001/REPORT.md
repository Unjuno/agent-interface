# Issue #6089 T0 — release-extended reachable-tube method result

**Disposition: `PASS_METHOD_SCOPED`.** The one-shot candidate and independent auditor both exited 0. The auditor independently enumerated raw paths, reproduced all in-bound reachable state sets at every active and release-in-flight prefix, and verified the largest-safe-horizon decisions and refusal gates. This is an exact finite-model method result only.

## Allocation and scope

- Allocation: `ROBUST-TUBE-6089-T0-20261001-01`
- Frozen main/base: `6cd70ad4bfad74e11658057bf024918bffb24add`
- Source freeze commit: `3774fac3eea179bb9be44f78e069651c25e2ab66`
- Branch: `research/robust-reachable-tube-6089-t0-20261001`
- Result path: `research/analysis/robust_reachable_tube_6089_t0_20261001/`
- Model: one-dimensional integer grid, initial closed integer intervals, one pre-authorized action per active slot, bounded independent disturbance choices, static/time-varying forbidden intervals, and explicit release lag. Every state is checked through release completion.
- Formal budget: candidate 1/1, independent auditor 1/1, reruns 0. Candidate and auditor stdout/stderr, raw JSON, process receipts, and hashes are retained beside this report.
- Environment: Windows host, Python 3.12.10. Docker Desktop's executable was present, but a bounded Engine version query timed out after 5 seconds and no container lease was assigned. No container, GUI, game, model, external service, or physical input was used.

## Result

The seven valid-model cases produced robust horizons: wide corridor 4; near upper boundary 0/YIELD; wide initial uncertainty 1; zero-slack release 0/YIELD; moving forbidden boundary 1; two-slot release lag 1; and release-in-flight boundary 1. Both stale-model and stale-target controls yielded with no policy schedules.

The release-boundary negative control began at x=28 with safe upper bound 30, zero commanded movement, disturbances {-1,0,+1}, and one release-in-flight slot. A two-slot active hold can reach x=30 at its observation deadline, but release can reach x=31; therefore h=2 is refused. The largest certified horizon is h=1, whose release completes at tick 2 without leaving the safe set.

In the wide corridor the selector admits the cap h=4; in the four constrained cases where fixed h=4 is refused, the robust selector still admits h=1. The nominal-point arm's longer request in the uncertain corridor is rejected by the common bounded-disturbance gate. The separate +3 disturbance stress exits the safe set at x=8, but +3 is outside the frozen {-1,0,+1} assumption and is not counted as an in-bound tube failure; it demonstrates why the hard bound must be valid.

## Interpretation and limits

This supports only that, for this finite one-dimensional contract, explicit set propagation through every active and release prefix can identify the largest admitted horizon and reject stale assumptions. It does not establish that disturbance bounds are valid for any real app, game or operating system. There is no measured action-to-effect behavior, actual hold occupancy, observation/capture cost, per-tick tracker-probe cost, runtime/CPU timing, task outcome, model cost, or human comparison. The experiment does not establish fewer real observations, better task performance, or safety outside its declared state/action/disturbance model; it is not a comparison against #6061's intermittent controller.

## Independent checks

Nine pre-freeze construction tests passed. Mutations for omitted prefix, ignored release lag, stale allocation identity and underestimated disturbance support were rejected. The formal auditor does not import candidate code and independently expands full disturbance paths. The out-of-bound stress is explicitly separated from the in-bound guarantee.

Source, raw outcome, and receipt SHA-256 identities are recorded in `RUN.json`; exact raw candidate and audit objects and their standard streams are retained in `formal/`.
