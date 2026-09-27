# Cache decision epoch/completeness model check — exploratory

Issue: #2928. This adds a distinct model dimension to the prior #5086 finite decision-order check; it does not rerun, replace, or revise that result.

## H / T / D / C / U

- **H:** The #5086 candidate predicate (recommend REACQUIRE iff effect is confirmed no-effect, freshness is current, and receipt is exact) is incomplete when request-origin epoch and dependency-completeness evidence are modeled. A stricter oracle derived from #2928's invalidation/default rules permits that recommendation only when the request epoch matches and dependencies are complete.
- **T:** Exhaustively enumerate 3 effect states × 3 freshness states × 3 receipt states × 3 request-epoch states × 2 dependency-completeness states = 162 combinations. Compare the prior candidate predicate with the stricter predicate. Two local CPython invocations were used: the original exploratory run and a provenance-label correction run; the decision logic was unchanged and both produced the same counts/counterexamples. Runtime: Windows host Python 3.12.10; exact corrected source `model_check.py`, SHA-256 `4fcc058cce85f56191efc8935f7bd563b3fdafdee3d4601fdcfa391e075451b2`. Docker Desktop was not used because the active #5074/#5082 shared lane had not released its slot.
- **D:** The corrected run asserts 162 total rows, six prior-rule REACQUIRE recommendations, one oracle-permitted recommendation, and exactly five candidate recommendations outside the stricter gate. This is `MODEL_RULE_INCOMPLETE`, not an implementation FAIL or lifecycle PASS.
- **C:** The oracle is a chosen formalization of #2928: request-epoch mismatch/missing cannot be treated as current reuse evidence; incomplete dependency provenance blocks a positive REACQUIRE recommendation. Enumeration checks predicate consistency, not policy optimality or implementation conformance.
- **U:** No existing cache implementation was invoked. No cost, lifecycle, receipt/effect linkage, GUI/application outcome, or cross-surface behavior was measured. This does not meet #2928's required experiment or PASS gate. The result is exploratory and was not preregistered.

## Provenance correction

The first exploratory output used the key `source_sha256` for a hash of the descriptive predicate ID, not the executable file. That original commit remains in this PR's branch history. The reviewer-identified ambiguity is corrected in the current source/output as `predicate_id_sha256`; the executable-file SHA-256 is recorded separately above. No predicate, state, result, or interpretation changed.

## Corrected result

```json
{"predicate_id":"cache-epoch-cross-product-v1:effect3*freshness3*receipt3*request_epoch3*dependency_completeness2;old=none&current&exact;oracle=old&same&complete","predicate_id_sha256":"0779f1830543a70a73b4f072d6dbc5103391439eeafb22def6d51162869ad84a","rows":162,"old_rule_reacquire":6,"oracle_allowed":1,"disagreement_states":5,"counterexamples":[["no_effect","current","exact","same","incomplete"],["no_effect","current","exact","changed","complete"],["no_effect","current","exact","changed","incomplete"],["no_effect","current","exact","missing","complete"],["no_effect","current","exact","missing","incomplete"]],"decision":"OLD_RULE_UNDER_SPECIFIED_FOR_EPOCH_AND_DEPENDENCY_COMPLETENESS"}
```

Five prior-rule recommendations rejected by the stricter oracle:

1. no_effect / current / exact / same epoch / incomplete dependencies
2. no_effect / current / exact / changed epoch / complete dependencies
3. no_effect / current / exact / changed epoch / incomplete dependencies
4. no_effect / current / exact / missing epoch / complete dependencies
5. no_effect / current / exact / missing epoch / incomplete dependencies

The only permitted state is no_effect / current / exact / same epoch / complete dependencies. No claims are made about the appropriate action among DISCARD, YIELD, or a separately initiated reacquisition in other states.
