# Predictive safety filter T3 — held-out compositional intent predicates

**Disposition: PASS_HELDOUT_COMPOSITION_SCOPED.** This is an exhaustive, deterministic host construction, not a runtime or product-safety result.

## Frozen design

From main 1ddbe03f93556d6db3eb61a72fa1148bd031a596, the frozen study enumerated every length-4 sequence over eight action symbols under four contracts: ORDER+REQUIRES, ORDER+MUTEX, REQUIRES+MUTEX, and all three. This yields 16,384 cases. The symbols differ from T2's SUBMIT/CLOSE example. The same fixed risk budget (10), action costs, and action order apply to both policies.

The baseline admits the longest risk-budget prefix. The semantic filter additionally checks each prefix against the declarative rules and stops before the first unsafe prefix. It never reorders or substitutes actions.

## Result

- Independent replay matched the complete runner output for all **16,384/16,384** cases; the case digest matched `26a83ce4864bc7a1`.
- The risk-only baseline admitted unsafe prefixes in **7,188 cases**, with **16,666** unsafe prefixes counted.
- The semantic prefix filter admitted **0 unsafe prefixes**. It completed **3,242/3,242** proposals that were fully safe and within budget; false blocks on that set were **0**.
- On this synthetic utility scale, admitted utility was **157,852** for risk-only and **101,459** for semantic filtering. The difference reflects blocked unsafe tails and is not a real task-quality comparison.
- Six direct predicate controls passed; unknown-schema and malformed-predicate controls returned UNKNOWN with zero admitted actions.
- The independent auditor rejected **4/4** mutated-result controls.

Raw JSON SHA-256: `33602cf641453f282a84e93925f3b5a7117d1455eac27edfed1cc3d1b7971531`.

## Scope and limits

Execution and independent replay ran in separate Codex functions.exec V8 isolates with standard JavaScript only and no filesystem writes. No GPU, Docker/OrbStack, model, GUI/input, external effects, or user task were involved. The rules, actions, utilities, and risks are synthetic; the result does not validate an application abstraction, runtime safety, task benefit, or a general viability guarantee.

The initial unfreezed audit source had a syntax error detected by syntax-only compilation and corrected before source freeze. No enumeration ran against that draft. Its original and corrected contents remain in branch history; the corrected frozen source was read back and syntax-checked before the single run.
