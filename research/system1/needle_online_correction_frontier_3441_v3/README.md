# Needle online correction frontier — Issue #4829

Formal successor of construction-only Issue #4826; it uses fresh seeds and does not rewrite the construction signal or Issue #4824's uninformative HOLD.

## Frozen question

Does a single shared rank-2 online correction adapter acquire the opposing B mapping while losing candidate-A competence, even though an immutable base preserves A? Three fresh seeds; A/B accuracy and cross-entropy are evaluated at the start and after every one of 32 balanced unique minibatch arrivals.

The binary task feature is coordinate 0. Coordinates 1–7 are seeded uniform nuisance values. A's target is coordinate 0; B's target is its complement. Each 8-row minibatch has four examples from each class. The adapter starts with an exact-zero second factor, so candidate predictions initially equal the frozen base.

## Decision

- `FAIL_ONLINE_CORRECTION_FORGETTING` if B reaches 0.90 while candidate A drops below 0.90, with independent untouched-base A >=0.90.
- Scoped PASS requires all seeds to pass every frozen integrity/quality/guard/audit gate in Issue #4829.
- No optimizer tuning or retry after the one formal training invocation.

## Construction evidence

Issue #4826 construction used seeds 67117/67229/67341 and is not formal evidence. The separate raw output, audit, and metrics remain linked from #4826. It motivated—but did not modify after formal execution—the preregistered discriminator and fresh-seed confirmation here.

## Reproduction

See `FREEZE.json` for source SHA-256, image digest, and resource/network boundary. Run `test_needle_frontier.py` as construction-only; then exactly once invoke `needle_frontier_study.py --output /out/raw.json` inside the specified Docker configuration. Run `needle_frontier_audit.py /out/raw.json` in a second container mounting `/out` read-only.

No Astra, GUI, external effects, provider/network, or action authority are in scope.

