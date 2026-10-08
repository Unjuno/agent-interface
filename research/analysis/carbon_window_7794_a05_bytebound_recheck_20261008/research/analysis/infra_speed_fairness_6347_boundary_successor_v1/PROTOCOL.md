# Issue #6347 — explicit batch-boundary successor

## H / T / D / C / U

**H.** A bounded first-ready-plus-five-tick grouping rule is discontinuous at its close boundary: changing only one equal-rights intent's scheduler-availability time from just before to just after close changes group membership and may change the winner. Aggregate delay-swap insensitivity does not establish boundary robustness.

**T.** Use a new deterministic no-model fixture with A ready at tick 0, equal grants/priority/rights, and B's exogenous readiness at tick 4 or 6. The batch closes at tick 5 and rotates from a declared pointer. Emit all offered IDs, readiness, close tick, collected IDs, deferred IDs, selected winner, pointer before/after and status. Include the paired before/after controls and twelve repeated windows alternating the two phases. A separate synthetic strategic-delay pair fixes eligibility at tick 0 but varies B's submission time to tick 4 or 6. Compare batch outcome with FRFS; do not describe simulation as an actual strategic participant.

**D.** `PASS_METHOD_SCOPED` requires an independent exact reconstruction of all emitted fields and rejection of four frozen mutations (hide a collected contender, include a late contender, forge the winner, corrupt the rotation pointer). The boundary hypothesis is supported only if the 4→6 tick change moves B from collected to deferred and changes the winner under the frozen B-first pointer, and the twelve-window output retains every attempt. Any missing contender/late entry or disagreement is FAIL/HOLD. No claim that rotation is normatively fair or deployment-ready.

**C.** A batching rule's decision right may be illegitimate; timestamp uncertainty or an atomic safety deadline could require HOLD/ordinary admission, not a winner. Five ticks is a chosen synthetic unit, not a recommended production delay.

**U.** Synthetic event ordering only. No synchronized real clocks, network, human behavior, strategic actor, GUI lease, safety, throughput or product result.

## Freeze / execution

The fixture fixes W=5, A-ready=0, B-ready in {4,6}, and initial pointer B. Each run is deterministic and all repeated opportunities remain in the denominator. Construction precedes preregistration. Formal candidate and independent raw-only auditor each run once in separate pinned OrbStack containers, with network disabled and read-only inputs; no retries. If main/source/image/path changes at launch, record STOP and do not launch.

