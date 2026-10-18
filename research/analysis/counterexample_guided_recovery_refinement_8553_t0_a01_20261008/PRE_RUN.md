# Issue #8553 T0 A01 — pre-registration

## Status

Frozen finite-method experiment; no candidate or audit invocation has occurred. This package is a new, additive allocation for the abstraction-adequacy question in [Issue #8553](https://github.com/Unjuno/agent-interface/issues/8553). It does not modify #8527's A01/A02, consume their allocations, or use the shared WSLc lane. The experiment runs directly with local CPython 3.12.10 and the standard library; it requires no Docker, WSLc, model, GUI, network, user data, or external action.

## Source and scope

- Clarke, Grumberg, Jha, Lu & Veith, “Counterexample-Guided Abstraction Refinement,” CAV 2000, DOI [10.1007/10722167_15](https://doi.org/10.1007/10722167_15).
- Chadha & Viswanathan, “A Counterexample Guided Abstraction-Refinement Framework for Markov Decision Processes,” arXiv:0807.1173 (2008), [arXiv](https://arxiv.org/abs/0807.1173).

These sources establish counterexample validation followed by abstraction refinement as a verification pattern, including an MDP framework. They do not establish that any GUI's hidden state, observation predicates, or recovery policy is represented by this fixture.

## H / T / D / C / U

**H.** In the frozen five-case finite partially observed transition fixture, counterexample-guided observable refinement will correct a planted spurious-loss verdict using one admissible predicate (versus all three safe predicates in fixed-fine), reject a planted optimistic false-recovery witness without any false `RECOVERABLE` claim, retain genuine non-recoverability and action-equivalent aliases, and return no recovery before the finite deadline.

**T.** Use `fixture.json` (21 concrete states across five independent worlds; actions are deterministic; maximum horizon 2). Exhaustively solve the finite belief-policy game under: (A) coarse observations; (B) fixed-fine observation using every safe declared predicate; and (C) CEGAR that validates a coarse witness against the concrete transition system and may add only a safe, predeclared observation predicate. The deliberately optimistic `optimistic-action-union` arm is confined to the false-recovery case to seed a false-positive counterexample; it is not called a sound abstraction. Include a safe separating probe, an unsafe-only separator, a genuine no-recovery case, action-equivalent aliases, and deadline exhaustion. The independent auditor reimplements exhaustive policy evaluation from the frozen fixture and candidate raw output; it may not import candidate code. Freeze source, fixture, tests and invocation counts before one candidate run followed by one audit run. Construction tests are not formal invocations.

**D.** `PASS_REFINEMENT_METHOD_SCOPED` only if (1) the exact concrete oracle and independent auditor agree on all five cases; (2) CEGAR recovers the safe-separable case using exactly `p_color`, while fixed-fine uses `p_color`, `p_phase`, and `p_zone`; (3) the optimistic false-recovery witness ends `UNKNOWN`, never `RECOVERABLE`, because no admissible safe predicate separates the alias pair; (4) the genuine-loss, action-equivalent, and deadline cases receive their hand-frozen exact verdicts; (5) no policy depends on a concrete state ID or unsafe predicate; (6) refinement lineage is complete; and (7) all five frozen mutations are rejected. `FAIL_UNSOUND` for any false-recoverable result, hidden-state/unsafe-predicate use, or missed concrete counterexample. `FAIL_NO_ADVANTAGE` if safe refinement fails to recover the planted case or uses at least as many predicates as fixed-fine. `HOLD_AUDIT` for any independent reconstruction error or incomplete raw record. On any first formal command failure, preserve it and do not retry this allocation.

**C.** A conservative fixed abstraction that always returns `UNKNOWN` on ambiguous beliefs may be simpler, equally safe, and cheaper than finding/refining predicates; the refinement advantage may be an artifact of the authored fixture and its predicate cost model.

**U.** Deterministic hand-authored finite transition systems only. The concrete oracle has privileged state access for validation/scoring, not for the emitted policy; a real GUI may not expose a safe separating observation or complete transition model. Predicate cost is a synthetic unit count, not measured latency. No live recoverability, task success, deadline guarantee, safety, or runtime benefit follows.

## Frozen protocol

- Candidate: `python -B candidate.py --fixture fixture.json --output raw/candidate.json`
- Independent audit (only if candidate exits 0 and raw output is present): `python -B audit.py --fixture fixture.json --candidate raw/candidate.json --output raw/audit.json`
- Construction suite before freeze and after result capture: `python -B -m unittest -v test_construction test_audit`
- Required one candidate invocation, at most one auditor invocation, zero retries; no other formal commands.
- Fixed-fine cost is the cardinality of the full safe predicate set, exactly 3. CEGAR cost is the cardinality of predicates added by refinement, expected exactly 1 across this fixture. Unsafe `p_secret` is never in either safe set.
- Preserve exact stdout, stderr, return codes, candidate JSON, audit JSON, final source hashes and SHA-256 manifest. Do not derive any success claim from construction-test results alone.

## Inputs and source identity

The frozen fixture is `fixture.json`; the candidate/auditor/test interfaces are in `candidate.py`, `audit.py`, `test_construction.py`, and `test_audit.py`. Final SHA-256 and Git blob identities will be recorded after construction and before the one-shot candidate. Any source or fixture change after freeze invalidates this allocation; do not repair or rerun it.
