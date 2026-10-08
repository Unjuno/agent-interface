# Negative-query responsibility T0 — A01

Allocation: `NEGATIVE-QUERY-RESPONSIBILITY-8624-T0-A01-20261009`  
Issue: #8624  
Scope: deterministic finite Boolean target-query rules, local CPU only.

## Frozen question and endpoints

For a finite, fully specified stratified query, can exhaustive signed-fact intervention analysis recover the exact causes and minimum contingencies for an observed `NO_MATCH`, while positive-only justifications miss contingency-dependent negative explanations? Keep this diagnostic separate from coverage/completeness certification and action authority.

The query endpoint is `final_match_v1`. A fixture produces `UNKNOWN` when its declared query scope is incomplete; otherwise it produces `MATCH` iff at least one query disjunct is true and `NO_MATCH` otherwise. Each rule derives one Boolean head from a conjunction of signed facts or lower-stratum derived predicates. Rule strata must be strictly lower than any derived dependency. The finite mutable-fact universe and toggle set are explicit and identical in the freeze.

For a `NO_MATCH` assignment A, a fact literal X=x is a scoped actual cause when a permitted contingency W (a set of other mutable facts toggled from A) leaves the endpoint `NO_MATCH` with X=x but changes it to `MATCH` when only X is toggled. Its minimum contingency is the least |W|, and responsibility is defined here as 1/(1+|W|). The robustness radius is the minimum number of all permitted fact toggles that changes `NO_MATCH` to `MATCH`. These are finite-model definitions, not claims about real-world causation or frequency.

Three outputs are compared: (1) minimal positive query supports and the positive eligibility support summary; (2) the minimum complete outcome-flip sets without per-fact attribution; and (3) compatible boundary-pair enumeration for each signed fact over every allowed assignment to the other facts. The support baseline is deliberately positive-only; it cannot explain an absent prerequisite or an exception whose role depends on a contingency.

## Cases and thresholds

The nine fixed fixtures cover a monotone positive control, an absent prerequisite, a present exception, a contingency-only exception cause, two cases with identical positive eligibility supports but different negation outcomes, a radius-1 / designated minimum-contingency-2 discriminator, a 10-variable dense case over the 512-world explanation budget, and an incomplete-scope control. The 9-variable contingency fixtures remain within budget at 512 worlds. No seed or sampling is used; all permitted assignments are enumerated.

PASS requires exact candidate/auditor equality for every row, the expected monotone positive support, explicit false and true fact literals, equal positive eligibility summaries with different outcomes in the paired cases, a contingency-only exception cause absent from positive eligibility support, radius 1 versus minimum contingency 2, and explicit `UNKNOWN_TOO_LARGE` / `UNKNOWN_INCOMPLETE` dispositions. Any mismatch is FAIL; model-domain uncertainty is HOLD. Construction mutations cover fact polarity, intervention-domain expansion, same-stratum dependency, endpoint change, and omitted mutable fact. No candidate or raw-only auditor retry is permitted.

## One-shot execution

The source, input, protocol, and construction checks are hashed in `FREEZE.json` before candidate execution. Run `python3 -B candidate.py input.json candidate_raw.json` exactly once. Only on exit 0, run `python3 -B auditor.py input.json candidate_raw.json audit.json` exactly once. Preserve stdout, stderr, exit codes, raw bytes, audit bytes, and any failure unchanged. Construction checks are separate from those two frozen CLI invocations.

## Limits

This tests only an authored finite Boolean rule system. It does not establish that a screenshot, accessibility tree, DOM, native adapter, coverage certificate, query scope, or observed absence is complete or atomic. It grants no rescan, action, model, or live GUI authority; it estimates no real-world probability, cost, usefulness, latency, or safety.
