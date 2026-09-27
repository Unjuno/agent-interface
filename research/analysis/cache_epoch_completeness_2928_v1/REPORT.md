# Cache decision epoch/completeness model check — exploratory

Issue: #2928. This adds a distinct model dimension to the prior #5086 finite decision-order check; it does not rerun, replace, or revise that result.

## H / T / D / C / U

- **H:** The #5086 candidate predicate (recommend REACQUIRE iff effect is confirmed no-effect, freshness is current, and receipt is exact) is incomplete when request-origin epoch and dependency-completeness evidence are modeled. A stricter oracle derived from #2928's invalidation/default rules permits that recommendation only when the request epoch matches and dependencies are complete.
- **T:** Exhaustively enumerate 3 effect states × 3 freshness states × 3 receipt states × 3 request-epoch states × 2 dependency-completeness states = 162 combinations. Compare the prior candidate predicate with the stricter predicate. One local CPython invocation; no files, repository code, model, GUI, input, or network were used by the run. The exact executed source is `model_check.py`, SHA-256 `c3015fa471820da7c8a6ce282fa7063597f9b02136d0720fccb1359131e195fb`. Runtime: Windows host Python 3.12.10. Docker Desktop slot was not used because #5074/#5082 ownership had not been released.
- **D:** Model check asserts 162 total rows, six prior-rule REACQUIRE recommendations, one oracle-permitted recommendation, and exactly five candidate recommendations outside the stricter gate. This is `MODEL_RULE_INCOMPLETE`, not an implementation FAIL or lifecycle PASS.
- **C:** The oracle is a chosen formalization of #2928: request-epoch mismatch/missing cannot be treated as current reuse evidence; incomplete dependency provenance blocks a positive REACQUIRE recommendation. Enumeration checks predicate consistency, not policy optimality or implementation conformance.
- **U:** No existing cache implementation was invoked. No cost, lifecycle, receipt/effect linkage, GUI/application outcome, or cross-surface behavior was measured. This does not meet #2928's required experiment or PASS gate. The result is exploratory and was not preregistered.

## Raw outcome

```json
{"source_id":"cache-epoch-cross-product-v1:effect3*freshness3*receipt3*request_epoch3*dependency_completeness2;old=none&current&exact;oracle=old&same&complete","source_sha256":"0779f1830543a70a73b4f072d6dbc5103391439eeafb22def6d51162869ad84a","rows":162,"old_rule_reacquire":6,"oracle_allowed":1,"overgrant_states":5,"counterexamples":[["no_effect","current","exact","same","incomplete"],["no_effect","current","exact","changed","complete"],["no_effect","current","exact","changed","incomplete"],["no_effect","current","exact","missing","complete"],["no_effect","current","exact","missing","incomplete"]],"decision":"OLD_RULE_UNDER_SPECIFIED_FOR_EPOCH_AND_DEPENDENCY_COMPLETENESS"}
```

Five prior-rule recommendations rejected by the stricter oracle:

1. no_effect / current / exact / same epoch / incomplete dependencies
2. no_effect / current / exact / changed epoch / complete dependencies
3. no_effect / current / exact / changed epoch / incomplete dependencies
4. no_effect / current / exact / missing epoch / complete dependencies
5. no_effect / current / exact / missing epoch / incomplete dependencies

The only permitted state is no_effect / current / exact / same epoch / complete dependencies. No claims are made about the appropriate action among DISCARD, YIELD, or a separately initiated reacquisition in other states.
