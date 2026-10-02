# Issue #6615 T0 protocol — adoption-inclusive verified-work accounting

## Status and scope

This is a prospective, deterministic method-only allocation. It contains no
operator, installation, GUI, model, user artifact, measured onboarding time,
or product comparison. All costs and verification labels are authored synthetic
inputs. A T0 result can validate accounting and audit controls only.

## H / T / D / C / U

- **H:** A route that is faster after preparation can still fail to reduce
  adoption-inclusive cost through a short horizon of independently verified
  useful tasks. A frozen cumulative curve should expose this rank reversal
  without changing the prepared-route calculation.
- **T0:** Enumerate the six finite cases in fixture.json. For each route,
  preserve setup attempt, setup failure, repair, task opportunity, every task
  attempt, and the independently stipulated verification result. Report wall
  time and human effort separately. Compare (a) prepared-only cumulative cost,
  which excludes successful one-time setup cost, and (b) adoption-inclusive
  cost from setup start. Count a task only at its first independently verified
  useful completion; include failed-attempt cost before that completion.
- **D:** PASS_METHOD_SCOPED only if the raw-only auditor reconstructs the
  complete event inventory, both curves, all denominators, and every frozen
  no-crossing/rank-reversal/eligibility control; empty or unreachable N values
  remain explicitly not reached. The audit must reject dropped setup-failure
  cost, attempted-as-verified work, unsupported-host success, and omitted app
  repair. This validates arithmetic only, not actual setup cost or route value.
- **C:** The task mix, cost values, operator work, repair needs, and verification
  labels are invented. Real reuse may amortize setup quickly; setup may be
  negligible, automated, or required for only one route.
- **U:** Learning, carryover, supported-host eligibility, user preferences,
  privacy, task demand, installation failures, credentials, network/cache
  state, and population variation remain unmeasured. No finite T0 estimates
  adoption or general break-even.

## Frozen cases and decision interpretation

1. zero_setup_delta: no setup-cost difference; guarded route is faster in
   both curves.
2. setup_dominates_short_horizon: guarded is faster per prepared task, but
   its fixed setup cost keeps it slower for every N in the frozen horizon.
3. learning_rank_reversal: one failed task attempt is charged but is not
   useful work; later cheaper guarded tasks produce a prepared-only crossing
   at N=6 and an adoption-inclusive crossing at N=8.
4. setup_failure: failed setup time is charged; no prepared-only curve or
   verified task is fabricated.
5. app_change_repair: a version change triggers a separately charged repair;
   both pre-repair and post-repair costs remain visible.
6. unsupported_host: guarded route completes only three of four assigned
   tasks; N=4 remains not reached, never a success or zero-cost completion.

Crossing means the first N where guarded cumulative cost is strictly less than
direct cumulative cost after an earlier N where it was not less. Wall and human
cost crossings are computed independently. Comparisons are contiguous from N=1
and stop at the first N not reached by both routes; record that first unreached
N and never skip it to resume comparison later. A missing N is not imputed,
extrapolated, or removed from the assigned-opportunity denominator.

## Execution boundary

Formal candidate and auditor runs are each capped at one invocation, with zero
retries. Use only Microsoft WSLc with an already cached digest-pinned Python
image, no network, a read-only source mount, and distinct writable output
mounts. Candidate and auditor run in separate ephemeral containers. No Docker
or OrbStack substitute, image pull, GPU, model, GUI, or user input is allowed
for this protocol. Preserve resource warnings; configured limits are not proof
of enforcement. If the required WSLc host/image or an assigned CPU-only lane is
unavailable, record a pre-run resource HOLD and do not start either invocation.

The current Mac worktree's missing WSLc executable is an environment fact, not
a result about the hypothesis. No formal invocation has been made by this
protocol.
