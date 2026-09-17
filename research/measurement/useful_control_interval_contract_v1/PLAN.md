# Useful-control interval contract v1 — excluded construction

H: A measurement contract that represents physical key-up as an interval and authority as separate intervals can compute conservative physical/authorized occupancy bounds without equating program lifetime with actuation or independently useful effect.

T: Pure Python/std-lib, fixed adversarial cases plus 100,000 seeded random traces. Independent discrete brute-force oracle over 50,000 fresh traces. No repository state, GUI, model, provider, network, or task input. Construction only; no formal claim.

D: PASS construction iff lower<=upper, authorized<=physical, occupancy never exceeds model-wait width, simultaneous actuations are unioned rather than double-counted, malformed released-state evidence fails closed, and unbound/unscored effects are never upgraded to causally bound useful effects across all fixed/fuzz/oracle cases.

C: A simpler exact-release schema could make interval bounds unnecessary; real backend receipts may have wider or differently defined censoring; useful-effect causality may require richer lineage than an actuation ID.

U: Synthetic time traces only. This validates arithmetic/epistemic separation, not MAP01 efficacy, release hardware truth, or human tempo.

Construction result: fixed cases PASS; fuzz 100,000/100,000 PASS; independent brute-force 50,000/50,000 PASS. Formal allocation is not authorized by this file.
