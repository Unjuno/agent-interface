# MAP01 dual-lifetime recovery guard tradeoff v1

Status: **RETAIN development candidate: fresh observable cancellation + independent owner deadline. No general gameplay/safety claim.**

## Question

Can a recovery action carry two independent lifetimes at once: (1) a hard owner-enforced authority deadline and (2) an earlier observable health guard, without destroying an already-useful attack effect?

The runtime source is the retained `9e6d5ecd...` ViZDoom/X11 stack. The saved `map01-threat-contact-v2` fixture starts at controller-visible health 97. Each matched arm runs the same two-step recovery during a simulated 4.5 s planner wait: `Up+space` for 1 s, then continued `space`; the owner deadline is 4.5 s. Only the strict arm cancels on the first fresh typed health value below source health.

## Development history retained

- v1: outer timeout after 3/6 arms; separate async prelude also allowed source health to drift across matched arms.
- v2: moved source binding before the program and fixed health=97; outer timeout again, leaving one complete pair plus one guard arm.
- v3/v4: complete, but v4 exposed an analysis bug. The classifier compared absolute monotonic timestamps from sequential sessions; v3's PASS was order-favorable and v4's HOLD order-unfavorable. Raw outcomes remain unchanged.
- v5: classifier repaired to compare each arm's authority-end offset from its own planner-start clock. Fresh seed, deadline→guard. PASS.
- v6: same repaired condition, fresh seed, reversed guard→deadline order. PASS.

The valid evidence block is v5+v6 only.

## Valid results

| allocation | order | deadline authority end | guard authority end | guard - deadline | damage capture → empty | typed emit → empty | kill/death |
|---|---|---:|---:|---:|---:|---:|---|
| v5 | deadline → guard | 4528.307 ms | 4217.275 ms | **-311.033 ms** | 12.334 ms | 2.702 ms | 1/0 both arms |
| v6 | guard → deadline | 4528.709 ms | 4151.113 ms | **-377.596 ms** | 13.951 ms | 2.880 ms | 1/0 both arms |

Median guard-minus-deadline authority end is **-344.314 ms**. Median damage-capture→verified-empty is **13.143 ms**; typed-event-emission→verified-empty is **2.791 ms**. Both matched pairs preserve independent `KILL_COUNT_INCREASE`, zero deaths, no MAP01 exit, verified empty release, zero scorer leakage/missed-period failure, and terminal-score audit PASS.

A useful architectural detail is that the kill is observed *after* physical authority is already empty: about 301 ms after release in v5 and 375 ms in v6. Therefore input authority lifetime and application-effect lifetime are distinct. Cancelling future input does not erase already-caused effects.

## Decision

**Retain the dual-lifetime structure as a development candidate:**

- owner deadline is the independent worst-case authority cap;
- fresh observable guard may terminate authority earlier;
- program/effect reconciliation continues after physical release;
- cancellation, expected deadline expiry, and semantic task success remain distinct events.

Do **not** generalize `any health loss -> cancel` as the universal guard. This block covers one attack-oriented saved state with two valid one-pair allocations. Movement/navigation may require a different policy-relative validity predicate, and earlier adversarial evidence already shows simple guards can have harmful tails.

## H / T / D / C / U

**H:** dual lifetime can shorten unsafe authority without necessarily destroying a useful effect already in flight.

**T:** two separately frozen fresh one-pair allocations after measurement repair, reverse order, same exact saved state/source health, zero model calls, independent progress scorer and terminal score audit.

**D:** RETAIN as development candidate because both valid allocations end authority earlier and preserve 1 kill / 0 deaths. No population efficacy claim.

**C:** attack effects can persist after release; other action classes may not. A strict health guard may be too conservative for movement and too permissive for other threats. Shared-host scheduling affects timings.

**U:** n=2 valid matched pairs, one fixture/action family, CPU clock not pinned, no frontier model, no full-map objective. The next experiment should transfer the same dual-lifetime contract to a non-attack recovery with an independently scored task-relative continuation/termination predicate rather than tuning a health threshold on these outcomes.
