# Issue #8553 T0 A01 — counterexample-guided recovery refinement

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite synthetic fixture only. The candidate and independent raw-only audit each ran once (exit 0; retries 0). The independent auditor reconstructed all five cases with zero errors. Construction tests passed 6/6, including rejection of all five predeclared mutations.

This is not evidence of a real GUI's hidden state, safe observability, recovery, task success, deadline guarantees, runtime benefit, or general CEGAR efficacy. The predicate costs are synthetic unit counts. The finite model and its concrete oracle were authored together.

## H / T / D / C / U

- **H:** In five deterministic finite belief-policy cases, validate a coarse witness and refine using only safe declared predicates; resolve a planted spurious-loss case with fewer predicates than fixed-fine, abstain on a false-recovery witness, and preserve genuine loss, action-equivalent aliases, and deadline exhaustion.
- **T:** Exhaustively enumerate bounded deterministic policies (horizon at most 2) for coarse, fixed-fine, and counterexample-guided refinement over 21 states in five independent worlds. The optimistic action-union arm is deliberately unsound and exists only to seed a false-positive witness. Independent `audit.py` reimplements the robust finite oracle and validates the candidate output without importing `candidate.py`.
- **D:** `PASS_METHOD_SCOPED` iff all five oracle verdicts agree, the safe separator uses only `p_color` versus all three safe predicates for fixed-fine, the false-recovery case returns `UNKNOWN`, no unsafe/hidden-state policy evidence appears, lineage is complete, and all five mutations are rejected. Any false `RECOVERABLE` or unsafe/hidden-state policy is `FAIL_UNSOUND`; audit or custody defects are `HOLD_AUDIT`.
- **C:** A conservative `UNKNOWN` policy may be equally safe and cheaper; the apparent refinement advantage could be fixture-specific.
- **U:** Hand-authored deterministic finite models only; the privileged concrete oracle is for validation, not policy output. No external workload or environment was sampled.

## Result

| Case | Coarse | Fixed-fine | CEGAR | Refinement |
|---|---|---|---|---|
| Safe separating probe | NOT_RECOVERABLE | RECOVERABLE | RECOVERABLE | `p_color` (1 predicate vs 3) |
| Unsafe-only separator / planted false recovery | RECOVERABLE (optimistic, unsound arm) | NOT_RECOVERABLE | UNKNOWN | concrete counterexample; no safe separator |
| Genuine nonrecoverability | NOT_RECOVERABLE | NOT_RECOVERABLE | NOT_RECOVERABLE | none |
| Action-equivalent aliases | RECOVERABLE | RECOVERABLE | RECOVERABLE | none |
| Deadline exhaustion | NOT_RECOVERABLE | NOT_RECOVERABLE | NOT_RECOVERABLE | none |

The result supports the preregistered method gate for this authored fixture. It does not support a runtime or product claim.

## Reproduction and custody

Run from this directory with CPython 3.12+ and the standard library:

1. `python -B -m unittest -v test_construction test_audit`
2. The formal candidate was run exactly once: `python -B candidate.py --fixture fixture.json --output raw/candidate.json`
3. The independent audit was run exactly once: `python -B audit.py --fixture fixture.json --candidate raw/candidate.json --output raw/audit.json`

The frozen inputs, source SHA-256/Git blob IDs, stdout, exit codes and raw JSON are retained in this directory. The initial construction iteration exposed and corrected one optimistic-arm modeling mismatch before freeze; it was not a formal invocation. No candidate or audit retry occurred after freeze.

## References

- Clarke et al., [Counterexample-Guided Abstraction Refinement (CAV 2000)](https://doi.org/10.1007/10722167_15).
- Chadha & Viswanathan, [A Counterexample Guided Abstraction-Refinement Framework for Markov Decision Processes](https://arxiv.org/abs/0807.1173).
