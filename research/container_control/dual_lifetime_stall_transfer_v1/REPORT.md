# Cross-domain dual-lifetime stall-backstop v1

Status: **PASS_DUAL_LIFETIME_STALL_BACKSTOP for the rendered X11 fault-injection fixture.** This is mechanics evidence only, not DOOM/model/general safety evidence.

## Question

A task-relative visual guard can stop a stale movement policy when the controller is responsive. What happens when the guard loop itself stalls?

This experiment combines two independent validity mechanisms on the same input authority:

1. **semantic/task-relative guard** — after observation resumes, the pixel-derived marker predicate cancels Left when the target-relative continuation condition is invalid;
2. **owner deadline** — the independent InputOwner thread releases held input at a hard 240 ms deadline even if the controller/guard loop is not running.

The comparison injects a deterministic **340 ms guard-loop stall**. Both arms use the same rendered pixels, XTest Left input, visual predicate and independent hidden scorer. The only scientific difference is the authority cap:

- `GUARD_ONLY`: same guard with a loose 1000 ms owner cap, so cancellation cannot occur until the 340 ms controller stall ends;
- `DUAL_LIFETIME`: same guard plus a 240 ms independent owner cap.

The exact scorer state is never read by the controller; it is audited only after each arm exits.

## Construction history

Two construction failures occurred before source freeze and before the formal matched block:

- smoke-0 inherited the older tracker's exogenous drift, moving nominal initial `x=0.08` to about `0.129` before source capture. The source gate correctly refused it. Repair: disable exogenous drift so the fault injection isolates authority motion; source tolerance and authority thresholds were not widened.
- smoke-1 reached owner interruption but failed writing `stop.flag` because the arm output directory did not exist yet. Repair: create the arm directory at controller start. Scientific conditions were unchanged.

Smoke-2 then passed. The formal runner and preregistration were hash-frozen before the first formal pair.

## Frozen condition

- five alternating-order matched pairs;
- initial rendered position `x=0.08`;
- Left movement; exogenous drift disabled;
- existing target-relative deadband `x <= 0.02` as invalid continuation;
- controller/guard-loop stall: 340 ms;
- hard dual-lifetime owner deadline: 240 ms;
- loose guard-only owner cap: 1000 ms;
- independent harmful-overshoot metric: exact scorer time while held with `x < -0.02`;
- required pixel decoder error `< 0.03`;
- required terminal empty/balanced app-side input and owner-verified release in every arm.

## Formal first outcome

Formal runner exit: **0**. Decision: **`PASS_DUAL_LIFETIME_STALL_BACKSTOP`**.

| Pair | Guard-only harmful overshoot | Dual-lifetime harmful overshoot | Dual - guard | Guard hold | Dual hold |
|---:|---:|---:|---:|---:|---:|
| 1 | 210.933 ms | 97.363 ms | -113.570 ms | 343.242 ms | 239.465 ms |
| 2 | 194.746 ms | 97.463 ms | -97.282 ms | 346.531 ms | 239.387 ms |
| 3 | 196.356 ms | 81.094 ms | -115.262 ms | 345.876 ms | 239.238 ms |
| 4 | 195.280 ms | 97.403 ms | -97.877 ms | 345.673 ms | 238.961 ms |
| 5 | 211.090 ms | 97.589 ms | -113.500 ms | 344.209 ms | 239.559 ms |

Medians:

- guard-only harmful overshoot: **196.356 ms**;
- dual-lifetime harmful overshoot: **97.403 ms**;
- paired dual-minus-guard median: **-113.500 ms**;
- guard-only app hold: **345.673 ms**;
- dual-lifetime app hold: **239.387 ms**;
- release-position exact `x`: guard-only **-0.16715**, dual **-0.09544**.

Hard gates:

- 10/10 arms terminal empty and app key press/release balanced;
- 10/10 owner releases verified;
- dual release occurs before guard-loop resume in 5/5 pairs;
- guard-only release occurs after guard-loop resume in 5/5 pairs;
- dual owner reason is `expired` 5/5; guard-only reason is `cancelled` 5/5;
- max visual-decoder error: **0.00833**, below frozen 0.03;
- dual deadline -> owner verified-empty: 0.330--0.539 ms across pairs;
- hard-gate failures: 0.

## Diagnostic relation to the earlier 240 ms controller budget

A separate development diagnostic reran the exact earlier `container_x11_bounded_recovery_v3.py` source under a new output identity. Its nominal 240 ms controller-managed recovery holds were app-observed at roughly **252--261 ms**, and its three natural guard invalidations appeared about **252.5--260.8 ms** after key-down acknowledgement. By contrast, an independent 240 ms owner deadline yields about 239 ms app-observed holds and can preempt that later guard exposure.

This means a controller-side duration and a physical input-authority deadline are not interchangeable. The old guard exposure partly depended on capture-coupled duration overshoot. This diagnostic is not part of the frozen five-pair result and is not a relabeling of the earlier formal evidence.

## Interpretation

The semantic guard and owner deadline close different failure modes:

- the **guard** answers whether the action remains semantically appropriate when fresh evidence is available;
- the **deadline** bounds how long authority can persist when fresh evaluation is delayed or unavailable.

Neither should substitute for the other. A production interface should allow the owner deadline to terminate physical input independently, then continue observation/effect reconciliation after release.

## H / T / D / C / U

**H.** Under a deterministic guard-loop stall longer than the hard authority cap, an independent owner deadline reduces harmful movement overshoot relative to the same task-relative guard with only a loose cap.

**T.** Five alternating-order rendered X11 matched pairs, identical pixel path/guard/input/scorer except the owner deadline, one first formal execution after source freeze. Controller cannot read exact scorer state.

**D.** **PASS** at this fixture scope: all five paired harmful-overshoot differences are negative and every hard safety/measurement gate passes.

**C.** This improvement is expected under the injected stall; it does not prove that 240 ms is an optimal deadline, nor that the same deadline transfers to other tasks. A too-short deadline can suppress useful action before a semantic guard needs to fire; a too-long deadline weakens the backstop.

**U.** Synthetic one-dimensional tracker, Xvfb/XTest, no frontier model, no DOOM, fixed injected stall, shared host/clock not pinned. The result establishes architecture/failure-mode separation, not a universal timing constant.

## Next gate

Do not tune the 240 ms value on this fixture. The next high-information test is to bind a dual-lifetime contract to a **real planner-wait recovery whose deadline is derived from the action/lease contract rather than this synthetic threshold**, then test both responsive-guard and delayed-observation cases with independent useful/harmful scoring. For MAP01, the deadline/guard must be derived from observable policy semantics rather than copied from this tracker.
