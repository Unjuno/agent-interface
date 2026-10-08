# Frozen H / T / D / C / U — Issue #7418 T0

**H:** In the frozen skewed episode corpus, unqualified consolidation will
generalize the common safe outcome into a protected context, while an explicit
source-linked applicability envelope will preserve the forbidden exception,
retain common-case coverage, and abstain on contradictory/unrepresented cases.

**T:** Compare three proposal-only representations over 17 frozen queries:
exact episode retrieval; majority-derived unqualified skill; and a shared skill
with explicit exception/UNKNOWN clauses. The 12-episode source ledger contains
eight common-safe episodes, one rare but irrelevant high-contrast safe episode,
one rare forbidden protected-mode episode, and a conflicting safe/forbidden
pair for one ambiguous mode. Evaluate eight seen and four held-out common cases,
two protected cases (one held out), the specificity control, the contradiction,
and an unrepresented context. Use the exact frozen outcome oracle and the
allowlisted predicates `app`, `object`, and `mode`. Count proposal coverage,
false-safe generalization, exception recall, UNKNOWN/deopt behavior, source
lineage, and serialized representation cost. No action is executed.

**D:** `PASS_METHOD_SCOPED` requires independent reconstruction of all 51
representation/query rows; zero false acceptance of either protected query by
the exception-preserving representation; at least 90% common-safe coverage;
both contradictory and unrepresented queries classified UNKNOWN; all 12 source
episode IDs retained and each derived clause source-linked; all representations
within the frozen 12-record / 8192-byte budget; and rejection of four planted
corruptions. The episode-retrieval and unqualified baselines are diagnostics,
not themselves required to pass. Otherwise report the precise failed gate as
`FAIL_METHOD`.

**C:** Exact episodic retrieval may already be safe and affordable; fresh-state
guards may make consolidation unnecessary; the compact shared skill may not
justify its exception bookkeeping. A different vocabulary could change the
tradeoff.

**U:** Predicate meanings and the finite effect oracle are stipulated. No
model-generated abstraction, human memory process, real workflow distribution,
GUI, action admission, authority, task-success rate, deployment prevalence, or
safety guarantee is tested. Serialized JSON bytes are a storage proxy, not
tokens or model cost. The immutable episode ledger remains canonical and is
never deleted.

## Execution boundary

Host CPython standard library is the frozen runtime: Issue #7418 specifies a
finite no-model/no-GUI/no-network method test and says no container is needed.
The formal candidate and independent auditor each run once, only after issue
preregistration; retries are zero. Construction tests are separate from those
two formal invocations.
