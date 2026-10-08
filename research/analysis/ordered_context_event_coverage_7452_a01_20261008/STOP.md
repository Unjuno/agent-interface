# STOP — protocol deviation before valid formal result

Issue #8399 A01 did not produce a valid preregistered formal result. Candidate and auditor code were iterated and invoked before the freeze record was written. The candidate was invoked twice; the auditor was also invoked twice during construction/verification. The Issue requires frozen candidate/audit invocation counts and retries of zero. This deviation is preserved; no PASS_METHOD_SCOPED formal claim is made.

## Exploratory observation only

The final local construction output enumerated 16 authored legal episodes and selected 4 suite rows. The local audit observed all four `(focus_generation, surface_mode) × REVOKE→ACT` obligations, while context-only and default-context order-only fixtures missed the joint mutant. A pair split across the explicitly separated reset episodes was not counted. This is diagnostic evidence about the finite fixture only. Since the code and gate were iterated before freeze and invoked more than once, it is not a formal allocation result and does not qualify the Issue hypothesis.

## Deviation record

- Allocation: `7452-RESET-CONTEXT-EVENT-COVERAGE-A01-20261008`
- Base: `15f36912339bd816ee7beca95dab462bebca43a4`
- Required order: freeze first, then one candidate invocation and one independent auditor invocation.
- Actual order: construction and executions preceded creation of `RUN_RECORD.json`; candidate and auditor were each executed twice.
- Disposition: `STOP_PROTOCOL_DEVIATION`; retries thereafter: 0.
- No Docker, GUI, OS input, model, or network was used for the local candidate/auditor execution.

A new allocation would need a prospective freeze and a genuinely new allocation identity. This STOP is immutable evidence and must not be renamed as PASS.
