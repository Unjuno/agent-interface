# Issue #5855 deterministic shared-verifier route-addition T0

## H/T/D/C/U

- **H:** With a fixed sequence of offers, a route selected as faster under isolated latency estimates can worsen mean and tail verified completion when its work funnels into a shared verifier. A 50%-utilization admission cap should avoid the held-out regression; making verification route-disjoint should remove it.
- **T:** Deterministic discrete-event model, 16 fixed task IDs, alternating classes A/B, one shared observation service, two class-specific existing routes, one selectable local fast route, shared finite model service for the existing routes, one shared verifier, and one shared cleanup lane. Enumerate all 2^16 assignments per cell for an idealized central comparator and for maximum deadline feasibility. Six cells sweep offer interval {16 low, 8 held-out nominal, 2 overloaded} and fast-route verifier work {8,12}. Units are integer ticks. Fixed offers never change between policies.
- **D:** T0 passes only if (1) low-load all-fast greedy improves mean and p95 versus baseline; (2) held-out (interval 8, fast verification work 12) isolated-latency greedy is materially worse in mean and p95, with verifier work and queue wait identifying the shared bottleneck; (3) the disjoint-verifier negative control removes the regression; (4) the 50%-utilization cap avoids the regression with exact tasks, safety checks and releases; (5) the overloaded interval-2 cell has no assignment achieving 16/16 within the 32-tick deadline; and (6) an independent raw-only discrete-event enumerator exactly reconstructs all submitted policy traces and enumerates all 65,536 assignments in every cell. Otherwise retain FAIL/HOLD without rerun.
- **C:** The cap is a static conservative utilization ceiling, not a learned scheduler; idealized central routing has full finite-schedule knowledge. Service times are deterministic and fixed. Every task's effect, safety verdict and verified release are synthetic, exact and identical across paths.
- **U:** Synthetic finite-model mechanism only. No claim about repository runtime, real model tokens, application effects, real arrival distributions, fairness, stationary equilibrium, user workloads or production throughput. The disjoint control changes verifier topology/capacity by design. T1 is not authorized or run.

## Frozen cell constants

- 16 offers, IDs 0–15, class A for even IDs and B for odd IDs; arrival time is ID × cell interval.
- Deadline 32 ticks from each offer.
- Shared observation service: 2 ticks/task.
- Existing routes A/B each use shared model service 8 ticks/task, then a route-specific local server with 5 ticks/task, then 4 shared verifier ticks, then 1 shared cleanup tick.
- Optional F uses one local server with 4 ticks/task and no model call, then shared verifier work 8 or 12 ticks/task, then the same cleanup.
- Greedy selection uses unloaded route costs only: slow 8+5+4=17; fast 4+8=12 or 4+12=16.
- Cap selects a deterministic evenly spaced number of fast routes while targeting shared-verifier utilization ≤0.50, computed from the frozen interval and service times. It cannot bypass the mandatory verifier, exact effect score, or release.
- Disjoint negative control replaces the shared verifier with route-owned lanes; fast-path checks execute in parallel on 2 or 3 dedicated lanes, each 4 ticks. No cross-route verifier queue remains.
- Central comparator exhaustively minimizes total completion latency; ties use p95 and then ascending bitmask. A separate exhaustive maximum-on-time count checks deadline unsatisfiability.

## Execution

Local CPython deterministic candidate once, then independent raw-only auditor once. No model, network, Docker/OrbStack, GPU, GUI, input, or shared runtime. Docker is not used because an unrelated OrbStack guest/resource reservation remains active; this T0 requires only bounded host CPU. Frozen source hashes and the exact commands are in FREEZE.json.
