# Issue #6009 T0 formal result — FAIL_METHOD

Allocation: `ROUTE-SWITCHING-6009-T0-20261001-01`
Frozen preparation base: `b2e7221c3c374cacc7037515f2df1508e965ac81`
Scope: finite synthetic method test only. No runtime, live GUI, model, or product claim.

## H/T/D/C/U result

- **H:** Refuted for this frozen fixture. The preregistered switching-aware policy did not beat both comparators in the alternating case: sticky cost 22, switching-aware 27, and greedy 45 (greedy also missed the deadline). Hindsight DP cost was 22. This is not evidence that switching-aware policies generally fail.
- **T:** One candidate invocation and one independent raw-output audit, as frozen. Five scenarios, 15 tasks, three abstract routes. Both programs exited 0. Candidate and audit outputs are retained unchanged under `results/candidate-01/`.
- **D:** `FAIL_METHOD`. Audit errors: three deadline `effect_ledger` mismatches, missing `alternating_crossover`, and `deadline_fail_closed`. The deadline rows were refused before any task effect, but candidate output contains `effects: [null]`; this is a candidate ledger defect, not an auditor false positive. The audit's independently replayed effects for those rows are empty. All four planted mutation controls were detected (4/4).
- **C:** This cost table makes sticky optimal on the alternating sequence and the exact DP reference agrees at 22. On binding expiry, the switching-aware route chose C after B became ineligible and matched DP at 21. Those scoped observations do not repair the failed preregistered crossover or ledger.
- **U:** Costs are authored abstract units, not elapsed time, tokens, or real GUI work. C was already available, so a rent/compile comparator was inapplicable in this frozen model. No theorem, live eligibility, route correctness, or product benefit follows. Docker Desktop was stopped/unavailable at the start gate, and this task had no owner-bound container interval: this is host-only evidence, not a container reproduction. No retry or repair was made under this allocation's zero-retry freeze.

## Reproduction and integrity

Candidate command:

```text
python -B research/analysis/route_switching_costs_6009_t0_20261001/candidate.py --out research/analysis/route_switching_costs_6009_t0_20261001/results/candidate-01/candidate.json
```

Independent audit command:

```text
python -B research/analysis/route_switching_costs_6009_t0_20261001/audit.py --candidate research/analysis/route_switching_costs_6009_t0_20261001/results/candidate-01/candidate.json --out research/analysis/route_switching_costs_6009_t0_20261001/results/candidate-01/audit.json
```

Both returned exit code 0; scientific disposition is nevertheless `FAIL_METHOD`. Frozen inputs remain byte-identical to `FREEZE.json`:

| File | SHA-256 |
|---|---|
| `PLAN.md` | `83cbe891156348c6671a608b259a4fe951c6e43ed2b8cec2677ff5ff2b654ed5` |
| `scenarios.json` | `46e8750b8d1d80c8799cb0abb32783bd1f65d97ddf70dd046a601beda8b63aa1` |
| `candidate.py` | `cd131a821234a0e4435880bfd11e3a195500c5c9baf5e0aa762c506c93270abc` |
| `audit.py` | `6ec14f3371275aec83ad7a0d6e96595cd9eb883e0af31fb42db5b85c59c8ada8` |

Retained raw output hashes:

| File | SHA-256 |
|---|---|
| `results/candidate-01/candidate.json` | `d854924e16489a58b1948d90b56ad4ecee9552688afc0e05c700e4f9abbcc211` |
| `results/candidate-01/audit.json` | `ba464b0c35b195e157f462d71ed25d16010b844f360db0858114955f7f775419` |

Any correction to the null-effect ledger or policy is a new successor allocation and path; it must preserve these raw files and this result.
