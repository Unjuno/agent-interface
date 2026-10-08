# Issue #6580 T0c — exhaustive public-branch follow-up

Allocation: `MODEL-AMBIGUITY-EXHAUSTIVE-6580-T0C-20261002-01`  
Base main: `49144844b482026c33fcfbde7e2fd5f7bdc7762c`  
Branch: `research/model-ambiguity-exhaustive-6580-t0c-wslc-20261002`

This additive successor tests one narrowly identified coverage gap in T0b: every theta value in a public nature-first support must be enumerated, not represented by a single witness. Earlier allocations and their reports remain immutable. The independent live-evidence review remains `HOLD_MODEL_LIFETIME_UNIDENTIFIED`; T0c is only a finite synthetic method check.

## H / T / D / C / U

**H.** Exhaustive public nature-first branches cover every theta in the reconstructed support, use the matching abstract action, and introduce no unsafe dispatch. Agent-first reactive cases continue only for singleton support; ambiguous support yields without action. Null: a branch is missing/duplicated, an action fails the mapping, or an unsafe dispatch appears.

**T.** Deterministic finite enumeration across 3 lifetimes (FULL/ZERO/EVENT), 2 phases, 4 evidence states, and 2 contracts gives 48 scenario keys. Nature-first rows enumerate the full support; agent-first contributes one row per key, for 66 total branch rows (42 nature-first + 24 agent-first), plus 6 parameter-independent negative controls. One-time construction tests check exact counts, both ambiguous public values, ambiguous reactive yield, and mutations dropping/inverting theta=1. Candidate and independent auditor are separate WSLc invocations.

**D.** PASS_METHOD_SCOPED iff all 48 keys and all 66 rows are present exactly, each public branch equals reconstructed support with its corresponding action, every reactive ambiguous state yields, all continuations have only safe reachable theta, six controls continue safely, and both branch mutations are rejected in the construction stage. Missing or incomplete data is HOLD; any formal mismatch is retained as FAIL. No retries.

**C.** This is a small deterministic model, not a GUI/environment experiment or empirical estimate. The rules and toy action-safety mapping are stipulated. A passing result validates only branch completeness and the auditor against this finite specification.

**U.** No real session/model lifetime, responsive environment, user-visible outcome, task success, latency, product safety, or transfer claim. T1 remains HOLD; T0c does not authorize a T2 live test.

## Frozen rules

Support is `{theta}` for FULL plus valid same-session evidence or EVENT after the declared event plus valid post-event evidence. It is `{0,1}` otherwise, including all ZERO, missing, and stale cases. For NATURE_FIRST_PUBLIC, emit one row for each supported theta, publicly observe that theta, and take A for 0/B for 1. For AGENT_FIRST_REACTIVE, singleton support continues with the corresponding action; ambiguous support yields and dispatches nothing. Each of six lifetime/order negative controls uses a theta-independent safe action.

## Runtime and provenance

Use native WSLc 3.0.1.0, cached Python image `python@sha256:1ae5b32b33f502335ed9f5ee7afa4387192e9566b1328fc66da836c77c1cfb65`, `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`. Memory enforcement is requested but not claimed. Construction, candidate, and independent audit receive one formal invocation each, maximum; any nonzero result is retained and stops subsequent stages. Auditor input copy must be byte-identical. Exact source hashes and run receipts are recorded in this allocation.
