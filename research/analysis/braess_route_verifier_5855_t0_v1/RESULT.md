# Issue #5855 — frozen synthetic T0 result

**Disposition: `PASS_SCOPED_SYNTHETIC_ROUTE_ADDITION_COUNTEREXAMPLE`.** The held-out finite fixture contains a route-addition regression under shared verifier congestion, despite the added route having a lower isolated modeled cost. This is an exact result for the frozen simulator only; it is not evidence that the production runtime exhibits Braess's paradox.

## H / T / D / C / U

- **H:** Selecting a nominally faster local route for the same fixed offers can worsen end-to-end verified completion when it increases work at a shared verifier; an admission cap or resource-disjoint verifier can remove that regression in a bounded synthetic fixture.
- **T:** Six deterministic scenarios, 16 alternating-class offers each, identical offered IDs and arrivals across policies, deadline 32 ticks. Arrival interval ∈ {16, 8, 2}; new-route verifier work ∈ {8, 12}. The baseline uses the two existing class routes. The greedy policy selects the new route for all offers because its isolated modeled cost is lower. The capped policy enforces a 50% shared-verifier-utilization target; a separate idealized central policy enumerates all 65,536 assignments per scenario. Held-out case: interval 8 / verifier work 12. Controls: low-load benefit, resource-disjoint verifier, utilization cap, and overloaded deadline feasibility.
- **D:** `PASS_SCOPED_SYNTHETIC_ROUTE_ADDITION_COUNTEREXAMPLE`. Candidate and independent raw-only auditor each ran once and exited 0; no retries. The auditor independently replayed 96 scenario-offer rows and exhaustively enumerated 393,216 assignment vectors across the six scenarios; 408 assertion groups passed. On the held-out case, isolated modeled cost is 16 ticks on the new route versus 17 on the baseline route, but greedy all-new routing raises mean completion from 20 to 49 ticks, p95 from 20 to 79, on-time completion from 16/16 to 4/16, and verifier waiting from 0 to 480 ticks. Under the frozen cap, the admissible new-route share is 0, so the policy falls back to baseline metrics (20 mean, 20 p95, 16/16 on time). Idealized central assignment obtains mean 19.9375 and 16/16 on time. In the disjoint-verifier control, greedy mean is 11 versus baseline 20, with zero verifier waiting. At interval 16 / verifier work 8, greedy is beneficial (mean and p95 15 versus 20). In the overloaded interval-2 / verifier-work-12 case, exhaustive assignment finds a maximum of 6/16 on-time tasks, so the 16-task deadline target is infeasible in this fixture.
- **C:** Exact finite enumeration, deterministic synthetic stage-work values, same 16 offers per policy, shared serial verifier unless the declared disjoint control is active, fixed cleanup, deadline 32, no retries, no task-generation changes, no stochastic sampling. The idealized central policy has complete foreknowledge and is an optimization bound, not a proposed online scheduler. Candidate, audit, raw result, and logs are retained in this directory. Runtime: Windows 10.0.26200, CPython 3.11.9; one local host-CPU process at BelowNormal priority during the bounded 07:20–07:29 UTC allocation. No Docker/OrbStack, GPU, model/provider, network, GUI, input, or external task effect.
- **U:** This supports only a counterexample in this particular finite queueing model and the value of measuring shared verifier work in a future integrated comparison. It does not show that any deployed route is slower, that the cap is generally optimal (here it admits zero new routes in the held-out case), or that the mechanism transfers to live GUI agents. All exact-effect/release/safety fields are fixture assumptions, not observed task outcomes. Issue #5855 remains open; no live allocation or product claim is closed by this T0.

## Scenario summary

All latency and waiting values are synthetic ticks. `central` is the minimum-mean exact assignment among all 65,536 masks; the `max on time` column separately gives the best on-time count over that same complete assignment space.

| Offer interval | New-route verifier work | Held out | Baseline mean / p95 / on-time | Greedy mean / p95 / on-time | Capped mean / p95 / on-time | Central mean / p95 / on-time | Max on-time |
|---:|---:|:---:|:---|:---|:---|:---|---:|
| 16 | 8 | no | 20 / 20 / 16 | 15 / 15 / 16 | 15 / 15 / 16 | 15 / 15 / 16 | 16 |
| 16 | 12 | no | 20 / 20 / 16 | 19 / 19 / 16 | 19.5 / 20 / 16 | 19 / 19 / 16 | 16 |
| 8 | 8 | no | 20 / 20 / 16 | 15 / 15 / 16 | 20 / 20 / 16 | 15 / 15 / 16 | 16 |
| 8 | 12 | **yes** | 20 / 20 / 16 | **49 / 79 / 4** | 20 / 20 / 16 | 19.9375 / 20 / 16 | 16 |
| 2 | 8 | no | 65 / 110 / 3 | 60 / 105 / 3 | 65 / 110 / 3 | 42.8125 / 72 / 7 | 7 |
| 2 | 12 | no | 65 / 110 / 3 | 94 / 169 / 2 | 65 / 110 / 3 | 51.375 / 88 / 4 | **6** |

The capped policy admits zero new-route offers at interval 8 / verifier work 8 and interval 2 (the frozen utilization constraint is already binding); these cells are not evidence that a positive route share was safely optimized. No route assignment or threshold was changed after execution.

## Reproduction and artifacts

The frozen commands were run from this directory with the pinned interpreter:

```text
python -B candidate.py     # one invocation, exit 0
python -B audit.py         # one invocation after candidate exit 0, exit 0
```

`FREEZE.json` is the pre-candidate freeze committed as `f37d3adc281731af14df7c9f56f1256ff2475590`, pinned to main `7dbe196b8d1fb519139d15240ecb3f377a07b51d`. `candidate-output/candidate-result.json` is the complete 305,548-byte raw candidate output. `candidate.stdout` and `audit.stdout` preserve the command receipts; both stderr files are empty. `HASHES.json` records SHA-256 and byte sizes for frozen sources, raw output, receipts, and interpreter. The earlier preparation-only storage hold is preserved on Issue #5855; the successful allocation was independently gated after storage became available.
