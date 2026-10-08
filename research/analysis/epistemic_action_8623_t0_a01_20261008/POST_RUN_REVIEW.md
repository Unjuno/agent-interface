# Append-only post-run review — T0 A01

Allocation: `EPISTEMIC-ACTION-8623-T0-A01-20261008`  
Formal run: one candidate invocation and one auditor invocation; zero retries.

## Custody review

- The preregistered source/specification freeze and SHA-256 manifest were published before the formal run. Frozen candidate, auditor, fixture, oracle, test, and runner bytes were not edited after freeze.
- Candidate and auditor stdout/stderr bytes and process receipts are retained in `formal/`; the stdout byte counts and SHA-256 digests agree with `formal/RUN.json`.
- Auditor reconstruction covered all 18 case-arm rows. It independently reads raw output, fixture, and oracle; it does not import candidate implementation.
- The construction suite passed seven tests under normal and optimized Python. It exercised rejection of four separately mutated records. This is construction evidence, not an extra formal candidate run.
- The run was executed once on host CPython 3.12.10. No Docker/WSLc, network, model, GUI, or operating-system input was involved. There was no retry or second formal invocation.

## Interpretation review

Retain `PASS_METHOD_SCOPED` and `H_PASS_SCOPED` only for this finite, authored CPU fixture. AVAILABLE and PRESCRIBED both score 4/6 on task success, while AVAILABLE has one unnecessary safe probe and a 5/6 stopping score versus 6/6. This validates the predeclared diagnostic contrast inside the fixture, not the construct validity of the competency taxonomy for real agents.

## Residual risk / follow-up

Candidate policies and oracle share the intentionally authored case definitions, so this is vulnerable to self-confirmation and does not test independent task generation, blinded implementation, generalization, or real-world action costs. A future attempt should preregister an independently authored generator and blinded policies as a successor study; preserve this exact result and link the successor rather than retroactively changing the disposition.
