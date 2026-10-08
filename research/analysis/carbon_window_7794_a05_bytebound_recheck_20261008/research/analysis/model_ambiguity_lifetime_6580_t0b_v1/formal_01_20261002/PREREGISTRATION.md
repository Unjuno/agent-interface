# Issue #6580 T0b — decision-level finite game preregistration

Allocation: `MODEL-AMBIGUITY-DECISION-6580-T0B-20261002-01`  
Base main: `547cd5e64603de9235a036c0170ecb77016c1383`  
Branch: `research/model-ambiguity-decision-6580-t0b-wslc-20261002`

This is a distinct successor allocation to #6580 allocation 01. Allocation 01 is unchanged and remains only a finite representation audit. The parallel retained-data audit's `HOLD_MODEL_LIFETIME_UNIDENTIFIED` is accepted: this T0b is synthetic method discrimination only, not a way around the missing live evidence.

## H / T / D / C / U

**H.** In this declared finite safety game, a lifetime-explicit gate can preserve safe `CONTINUE` decisions supported by a fresh receipt under FULL or post-event EVENT stickiness while returning `YIELD` when a stale/missing receipt or ZERO/per-step variation leaves both regimes possible. A lifetime-unspecified conservative comparator may YIELD in cases where a declared persistent model plus valid receipt permits safe continuation. A point-from-prior comparator can select an action with an unsafe possible prefix when the uncertainty may have changed. Null: the distinctions do not yield a useful safe-continuation witness or expose any point-comparator risk.

**T.** Model-free deterministic WSLc CPU enumeration. Binary hidden parameter `theta∈{0,1}`; action A is safe only for theta 0, B only for theta 1. Cross 3 lifetime rules (FULL, ZERO, EVENT), 2 phases (pre/post declared event), 4 evidence states (valid theta 0/1, missing, stale), and 2 move/observation contracts (nature-first with current theta publicly observed before action; agent-first with responsive nature able to choose after seeing the proposed action): 48 decision rows. Add six parameter-insensitive negative controls. Candidate computes prior support, lifetime-explicit decision, lifetime-unspecified decision, and point comparator; it dispatches no actual effect. Independent auditor reconstructs every support/decision and safe reachable theta. Include seven construction mutations: discard FULL evidence; reuse ZERO prior evidence; commit EVENT too early; let stale evidence narrow; allow responsive nature to defeat a continuing proposal; permit unsafe dispatch; break a negative control.

**D.** `PASS_METHOD_SCOPED` only if all 48 rows and six controls match the independent enumerator, at least one explicit safe-continuation-over-unspecified witness and one point-comparator unsafe-possible witness are present, no gate CONTINUE has an unsafe reachable theta, and all seven mutations are rejected. Any false safe continuation or oracle mismatch is `FAIL_METHOD`; missing/incomplete inputs are `HOLD`. No behavior, probability, reward, or safety claim transfers beyond this exact toy game.

**C.** The two order labels include a deliberately declared observation contract (the nature-first current choice is public); thus this is not a pure order-only theorem or numerical replication of IJCAI-24. There are no stochastic kernels, optimization, unbounded histories, GUI state, or model decisions. A deterministic gate can be overly conservative or useful only because this fixture supplies the exact assumptions.

**U.** No real interface lifetime, live responsive counterparty, product safety, action authority, task success, latency, or token savings. Retained evidence still does not identify a real session's model lifetime. T1/T2 remain gated and unclaimed.

## Frozen rules

Prior support is `{0,1}` except (a) FULL plus valid same-session receipt, which supports its recorded theta, and (b) EVENT after the declared commitment event plus valid post-event receipt, which supports its recorded theta. ZERO never carries a previous-step receipt forward. Missing and stale evidence never narrow. Under `NATURE_FIRST_PUBLIC`, nature's current theta is selected from the prior support, exposed before action, and the gate chooses its matching A/B action. Under `AGENT_FIRST_REACTIVE`, a singleton support permits the matching action because the parameter cannot be changed under that frozen lifetime; a non-singleton support yields without dispatch because responsive nature may choose the opposite theta after seeing the proposal. Controls make the parameter irrelevant, so every declared rule/order continues with the abstract safe action.

An unspecified robust comparator YIELDs on agent-first rows and uses the public current observation on nature-first rows. The point comparator acts on the previous valid theta or defaults to 0; the auditor reports when an unsafe theta remains possible. This is a counterfactual abstract action only; candidate contains no effect dispatcher.

## Runtime, invocation cap, stop and provenance

Use native WSLc 3.0.1.0 and the already-cached digest-pinned Python image; `--pull never`, `--network none`, one CPU, uid 65534, requested memory 1G. Record exact runtime warning; do not claim memory enforcement. Construction, candidate, and independent auditor each receive exactly one formal invocation. No retry, source repair, or output replacement after formal start. Exact source/staged hashes, invocation counts, input-copy byte identity, and output receipts are in `FREEZE.json` and stage files. A nonzero or mismatching stage remains a retained STOP/FAIL.
