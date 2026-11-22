# T0 protocol — per-artifact GUI macro translation validation

Allocation: `UNJUNO-7827-TV-A01-20261005-01`  
Issue: #7827  
Base: `dccf55e264f434ca27f2948fe53be09919047819`  
Additive repository path: `research/analysis/gui_macro_translation_validation_7827_a01_20261005/`  
Execution: one pinned, cached WSLc Python 3.12.15 container; network disabled; no pulls; one CPU, 128 MiB configured. Resource-limit enforcement is not inferred from configuration.

## H / T / D / C / U

**H.** For this bounded DSL/ISA and finite context model, independent per-artifact translation validation accepts each valid pair and rejects all seven frozen semantics-drift mutations with replayable counterexamples; expected-example tests miss at least one mutation because they do not exercise adverse freshness/cancellation contexts.

**T.** Enumerate each macro against both target identities, fresh/stale observations, and cancellation at every visible-event boundary. Source constructs: sequence, target freshness guard, effect, wait, observe, release, abort, yield, and bounded repeat (max 2). Target constructs: CHECK, EMIT, WAIT, OBSERVE, RELEASE, ABORT, YIELD, CONTINUE, and stuttering INTERNAL. Compare exact visible traces including effect values/order, release, abort, wait/observation and yield events; only INTERNAL may stutter. Repeat is expanded before execution. An oversized repeat must return UNKNOWN without a certificate.

Frozen mutations: drop freshness guard; change effect target; reorder noncommuting wait/observe; remove cancellation release; hide a forbidden write in INTERNAL; convert YIELD to CONTINUE; alter an effect postcondition. Each has a valid source and one mutated target. The baseline executes only the predeclared nominal (fresh, correct-target, no-cancel) examples. The independent auditor is separately written and consumes raw candidate output plus frozen inputs.

**D.** `PASS_TRANSLATION_VALIDATION_METHOD_SCOPED` iff all valid pairs are accepted, all seven mutations are rejected with independently replayable counterexamples, oversized repeat is UNKNOWN without certificate, candidate/auditor certificates bind exact source/target/model SHA-256, and the baseline misses at least one registered mutation while validator catches it. Any soundness/validity mismatch is `FAIL_METHOD`; otherwise missing gate is `METHOD_FAIL_OR_INCONCLUSIVE`. No GUI/runtime authority follows.

**C.** Ordinary independent action/effect verification or path-level equivalence may suffice; source intent may be underspecified; an incomplete model or shared semantic mistake may dominate.

**U.** Finite traces do not prove unbounded loops, scheduler/timing behavior, OS/backend semantics, application effect truth, or source-intent correctness. Both interpreters are scoped to `model.json`; independent implementation and mutations reduce, but do not eliminate, common-mode risk.

## Freeze / run rule

Construction checks are separate from the formal candidate and audit invocations. Freeze all source/input/test/runner hashes before formal execution. Candidate exactly once, audit exactly once, no retries. Preserve first outcomes, stderr/stdout, exit codes, hashes, and WSLc warnings. The formal result has no live GUI, model, user-input, game, product, or safety implication.
