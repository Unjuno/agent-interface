# Issue #8500 T0 A01 — preregistered protocol

## H / T / D / C / U

**H.** In this finite constructed analogy corpus, structured counterexample/boundary memory will produce fewer invalid proposals than both no-memory and prose-only arms, while preserving the valid-candidate recall of the no-memory arm and reopening all four candidates whose target applicability envelope explicitly changes.

**T.** With the fixed non-agent scorer in `candidate.py`, evaluate the same eight target cards and 24 source/candidate mappings in the same within-card candidate order under three isolated conditions: no prior rejection memory, prose-only rejection notes, and relation-keyed counterexample records with explicit boundary predicates. The six rejection records cover objective, observability, authority, reversibility, failure/recovery, and implementation-only analogies. Run four additional changed-envelope controls for R01–R04. Randomize condition order per target using the frozen seed. Every candidate receives one lookup slot and a 64-word-unit visible-context budget; no arm label is included in scorer-visible input. Retain all decisions, including `UNKNOWN`, and never remove a candidate from the denominator. The independent auditor recomputes corpus membership, relation truth, budgets, randomized schedule, metrics, and five corruption controls without importing candidate code.

Construction tests and mutations run before freeze. After freezing the protocol, fixture, candidate, auditor, and test-source hashes, the formal candidate and formal independent auditor are each invoked once. No humans, LLMs, web search during scoring, live GUI, application, external action, or deployed memory are used.

**D.** `PASS_METHOD_SCOPED` requires fewer invalid proposals in the structured arm than in each control; structured valid-candidate recall no lower than either control; all four changed-envelope positives proposed after a fresh check; identical candidate exposure and budgets; zero independent audit errors; and rejection of all five frozen corruptions. `FAIL_NEGATIVE_SUPPRESSION` if any changed-envelope positive is automatically excluded or not proposed by the structured arm. `NO_INCREMENTAL_VALUE` if structured does not strictly reduce invalid proposals versus both controls. Other corpus, schedule, budget, or audit-integrity failures are `FAIL_METHOD`. No label is an open-literature, human-review, or product result.

**C.** Fresh target-specific analysis may make rejection memory unnecessary; prose notes may suffice; retrieval may miss the relevant rejection; and a negative memory may suppress a candidate after its applicability assumptions change.

**U.** The scorer is a deterministic, hand-authored finite rule system and the corpus is designed. Its scores are not a model, human, literature-search, or idea-quality estimate. Whitespace word-units are not tokenizer tokens. No inference about creativity, real-world novelty, reviewer agreement, or Agent Interface performance follows.

## Frozen execution contract

- Intake main: `48560b7345a9922f125c9a375244d0e4f12b4f0d`.
- Issue: [#8500](https://github.com/Unjuno/agent-interface/issues/8500); parent/method neighbors reviewed: #8073, #1945, #5541, #701.
- Package: `research/analysis/analogy_rejection_8500_t0_a01_20261008/`.
- Runtime: local CPython 3.12.10 in the supplied Windows execution environment; standard library only; no container/WSLc/Docker invocation is required by this finite scorer. This is not a WSLc migration or runtime comparison.
- Candidate command: `python -B candidate.py --dir .`.
- Auditor command: `python -B audit.py --dir .`.
- Formal roles: candidate 1, auditor 1, retries 0. Construction invocations are separately recorded.
- Seeds: condition schedule 850001–850008; changed-envelope schedules 850101–850104.
- Changed-envelope controls: target cards T01–T04 only.
- Raw output is immutable after each formal invocation. Any code/input change after freeze invalidates the allocation and must not be silently retried.
