# Issue #4680 reduced deterministic compile-down — allocation 01

Status: frozen before the one Docker study invocation. This is the explicitly permitted reduced deterministic rung because the learned prerequisites are unavailable; it is not the Issue's adapted-Needle comparison.

## H / T / D / C / U

**H.** For one bounded, externally declared deterministic skill, compiling its decision rules into an immutable finite decision table preserves the independent policy oracle over the full declared finite state space, including required YIELD and no-action boundaries. Invalid candidate packages must not replace the active package.

**T.** Enumerate the complete 256-row product: four intents × four evidence states × two progress values × two completion values × two generation-freshness values × two forbidden-effect flags. Compare (1) a direct rule evaluator, (2) a precompiled table lookup, and (3) a separately implemented oracle. Run a fixed negative-control set for invalid intent, stale generation, missing/ambiguous evidence, forbidden effect, package authority expansion, and failed candidate activation. One study invocation in Docker; a separately invoked raw-only audit recomputes the outcomes.

**D.** `PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED` iff exactly 256 unique rows reconcile, all three decision paths agree with zero oracle mismatches, required boundaries yield/no-op as declared, invalid authority expansion is rejected, and failed activation leaves active bytes/digest unchanged. Any semantic or authority mismatch is FAIL. Missing identity/row/raw/audit evidence is STOP/HOLD. No latency gate is defined and no speed claim is allowed.

**C.** Same immutable package, state rows, and action vocabulary for all three paths; no model, GUI, input, provider, network, or runtime authority. Oracle is code-separated from the candidate evaluator/compiler modules. Docker source read-only, network disabled, pinned cached image, bounded resources.

**U.** Synthetic finite policy semantics only. This does not test Astra demonstrations, Needle adaptation, learned semantic branching, GUI transfer, application effects, execution timing benefit, amortization, or the full #4680 hypothesis. The actual Needle adaptation prerequisite is currently not met (#4205/#4576: 0/7 exact candidate cases); the fast learned backend prerequisite is also not met (#4203/#4584: pre-inference acquisition STOP). This reduced result cannot satisfy either prerequisite.

## Frozen package and policy

Package `skill_id=bounded-progress-v1`, `intent_version=1`, actions `{CONTINUE,CORRECT,WATCH,YIELD,NO_ACTION}`, forbidden effect `{SUBMIT}`, required YIELD evidence states `{MISSING,AMBIGUOUS,STALE}`, and invalid intent IDs fail closed. For valid fresh evidence: completed -> NO_ACTION; TRACK -> CONTINUE if progressing else CORRECT; STABILIZE -> CORRECT if not progressing else CONTINUE; WATCH_ONLY -> WATCH; OUT_OF_SCOPE -> YIELD. Any forbidden-effect flag yields. Generation mismatch yields.

No correction or post-outcome tuning is permitted. The study does not measure latency.

## Exact environment and command

- Image ID: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`python:3.12-slim`, linux/amd64).
- Command: `python -B /study/study.py --freeze /study/FREEZE.json --output /out/RESULT.json`.
- Docker constraints: `--pull=never --network none --read-only --cpus=1 --memory=512m --pids-limit=32`; study mounted read-only and fresh output directory writable.
- Formal study invocation count: exactly one. Independent auditor is a separate Docker process and does not import study/compiler/oracle modules.
