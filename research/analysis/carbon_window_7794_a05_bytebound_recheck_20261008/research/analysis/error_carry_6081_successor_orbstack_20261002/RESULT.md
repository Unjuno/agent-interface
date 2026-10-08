# T0 successor result — Issue #6081

## H / T / D / C / U

**H.** Under a constant rational per-slot intent and explicit constant-displacement action dictionary, cumulative-error scheduling can lower worst-prefix squared displacement error against the stationary Euclidean-nearest action without increasing prefix-box violations, switch count, or release faults.

**T.** One frozen 10-case × 2-alphabet × 4-policy exact-rational run (80 rows), followed by separate independent raw reconstruction and a separately registered decision-gate audit. A = horizon-wide Euclidean-nearest fixed action; B = independent per-slot Euclidean-nearest without carry; C = cumulative error carry; D = release/no continuation. Every prefix, terminal error, switch count, envelope, refusal and release is retained.

**D.** `PASS_METHOD_SCOPED` by the independently rerun S6 decision audit against the original frozen criterion. S5's exact reconstruction matched all 80 candidate rows. A and B were identical in all 20 action-set/case cells. Among nine eligible, safe, nonrepresentable cells, C lowered worst-prefix squared error in 9/9. C had zero prefix-envelope violations, zero switch-limit failures, zero release failures, and no illegal action. A/B had two unique unsafe case cells; C had zero, so C did not increase safety violations. Outside-hull and unknown-calibration controls refused; exact and zero controls passed.

**C.** Rational-grid synthetic model only. 4-way and 8-way vectors are explicit fixture data; diagonal behavior is stipulated, not inferred from keyboard semantics. Python stdlib and OrbStack `python:3.12-alpine` ARM64 image; network disabled, source read-only, formal output separately mounted.

**U.** This does not demonstrate calibrated real inputs, application/game physics, acceleration/collision safety, OS timing, focus, task effect, model utility, human tempo, live key dispatch, or MAP01 progress. The prefix box is a synthetic constraint, not a safety proof for a real actuator. D models a zero-action schedule with declared release, not empirical OS key-up delivery.

## Interpretation and audit chronology

The main methodological result is partly a negative-control finding: with stationary action vectors, fixed slot duration, constant intent and Euclidean distance, A (choose one action for the horizon) and B (repeat the independently nearest action each slot) are the same policy. They are not two independent baselines in this model. Error carry beat their shared comparator on all nine safe, nonrepresentable eligible cells; no claim can be made that it beats two distinct methods.

On two near-axis cells the repeated-nearest baseline crossed the frozen synthetic envelope while the error-carry schedule stayed inside; this lowered rather than increased the number of violations. All comparisons use identical action alphabets and horizon. Cases where either baseline or C was unsafe were not used to count approximation wins.

Audit defects remain visible rather than being polished away: S4 candidate exit 0, first auditor `STOP_AUDITOR_SCHEMA_ASSUMPTION / NOT_EVALUATED`; S5 exact raw reconstruction succeeded but its gate implementation returned `FAIL_METHOD_OR_SAFETY_GATE` because it treated unsafe baseline rows as a fatal gate; S6 independently applied the frozen rule and returned `PASS_METHOD_SCOPED`. See each frozen manifest and output. S4/S5 evidence is unchanged; S6 is a new audit-only successor, not a candidate replay.

The result warrants retaining the error-carry comparator as a small synthetic method result and the A/B equivalence as a design correction. It does not authorize or justify transferring this algorithm to live input. A future live test needs its own authority, calibrated semantics, observed key release, dynamic safety envelope and independent effect oracle.
