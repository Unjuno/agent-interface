# Issue #6138 T0 — forward-equivalence discriminator

## H / T / D / C / U

- **H:** A prior-spend-only change cannot alter the exact forward-looking choice when every current and prospective operand is identical; a legitimate prospective-cost change may alter it. The pair checker must reject differences in artifacts, evidence, deadline, budget, safe-action set, or future cost.
- **T:** Ten authored finite cards, seven paired comparisons, exact rational arithmetic. The sink-only pair has prior spend 2 vs 200 and identical forward operands; a positive control raises only the future switch cost; six negative controls each alter one forward operand; one unresolved probability yields UNKNOWN.
- **D:** `PASS_METHOD_SCOPED`: independent auditor reconstructed 10 cards / 7 pairs with no errors. Low- and high-sunk cards both choose SWITCH (forward values 4 vs 5). The positive control chooses CONTINUE (4 vs 3). All six non-equivalent controls are refused as matched pairs; UNKNOWN remains UNKNOWN. Local tests 9/9.
- **C:** Candidate and independent auditor invoked once each in separate pinned OrbStack Docker containers; retries 0; network disabled, read-only root/source/input, 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges.
- **U:** No model, GUI, participant, user data or real route. Probabilities and payoff units are stipulated. This validates a finite discriminator only; it is not evidence for/against model sunk-cost bias and does not authorize T1 or production changes.

## Exact method result

With value = future success probability × reward − prospective action cost: CONTINUE = 1/2×10−1 = 4; SWITCH = 7/10×10−2 = 5. Both cards choose SWITCH despite prior irrecoverable spend 2 vs 200. In the positive control, only future switch cost rises to 4, making SWITCH=3 and CONTINUE=4, so the choice changes rationally. Six paired-card controls vary one actual forward operand and are rejected as sink-only matches.

## Stop

T0 method construction is complete. Any model-facing T1 requires a new explicit allocation, matched stateless cards, blinded/frozen interpretation, balanced order and authority. No historical route or model result is backfilled.
