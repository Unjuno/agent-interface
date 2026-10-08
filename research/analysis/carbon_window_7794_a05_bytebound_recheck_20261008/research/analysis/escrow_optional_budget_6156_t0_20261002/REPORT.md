# Issue #6156 T0 — escrowed optional-resource budget

## Result

**PASS_METHOD_SCOPED.** Frozen candidate and independent auditor each ran once in separate bounded OrbStack Docker containers; retries 0. The independent audit regenerated and matched the full reachable state and transition sets: 9,988 states and 27,748 transitions through depth 6, global budget B=4. Construction tests passed 13/13 before formal freeze. Raw output, hashes, and exact commands are recorded in RUN.json and SHA256SUMS.

## H / T / D / C / U

- **H:** Preallocated fungible optional rights preserve B while reducing per-use coordination for balanced two-worker demand; skew/crash can strand rights and reduce availability.
- **T:** Two workers, four unique rights, generation-fenced state machine; bounded consume/crash/restart/reclaim/surrender/transfer-ACK operations; independent full state/edge enumeration. Controls include lost/late receipt heartbeat reclaim, old-generation restart, duplicate and delayed prior-transfer ACK, balanced and skew demand, mandatory verifier after optional exhaustion, unavailable mandatory lane, and work-role mislabeling.
- **D:** PASS requires exact enumeration digest agreement, no conservation/identity/fencing violations, correct positive/negative controls, and detection of planted corruptions. It is method-scoped and cannot qualify implementation or product behavior.
- **C:** Central batching may be simpler; rights stranded after crash or demand skew may outweigh saved coordination.
- **U:** One issuer, durable journal, unique IDs, true numeric fungibility and the frozen state machine only. No distributed-runtime, elapsed-time, GUI, live model, task-effect, or general stability evidence.

## Observed finite controls

Balanced demand A=2/B=2: escrow completes 4/4 optional units with two setup coordination round-trips; central per-use admits use four round-trips. Same modeled completion, lower coordination count; this is not a wall-clock latency estimate.

Skew A=4/B=0 and B crash/restart: escrow completes 2/4 and strands two rights; central baseline completes 4/4. No surrender means no reclaim. Restart generation advances to 1 and the old ticket is rejected. A planted timeout-reclaim mutant permits five actual consumes against B=4 and is flagged as unsafe.

Transfer tests accept the first fenced ACK, reject a duplicate ACK, then reject the delayed ACK from an older transfer after that same right has moved again. Four right identities remain conserved. Optional exhaustion does not gate an independently available mandatory verifier; if that lane has no capacity, the outcome is YIELD and consequential action is blocked. A stale-evidence request self-labeled optional is classified mandatory; routine recapture self-labeled mandatory remains optional; ambiguous role returns HOLD_ROLE_AMBIGUOUS.

## Construction note

Before freeze, construction enumeration exposed an ambiguity when historical acknowledged transfers and a new in-flight transfer referenced the same right. The candidate was revised to bind the active transfer ID directly to the right, and the independent auditor now checks that unique current reference. This was repaired before formal allocation; it is not hidden or counted as a formal PASS/FAIL row. The final frozen construction suite passed 13/13.

## Scope and handoff

No T1 was run. No optional resource was consumed outside the simulator. No GUI, model, external service, or task effect was involved. Formal evidence says only that this finite protocol model and its independent enumerator agree on the stated bounded state space and controls; arbitrary distributed implementations still require separate validation.

