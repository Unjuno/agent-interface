# Report

Status: `PASS_FOCUSED_REQUEST_VALIDATION_SCOPED`

The finite fixture enumerates 256 frame/request combinations. The candidate accepted 16 and rejected 240. An independent auditor recomputed the same 256-case oracle and obtained 16 valid and 240 rejected cases.

Required fail-closed properties held for the tested fixture:

- epoch mismatch rejected;
- identity mismatch rejected;
- non-uncertainty reason rejected;
- out-of-bounds and empty regions rejected;
- matching in-bounds uncertainty requests accepted.

The candidate run was executed locally with Python and no model, GUI, network, runtime, or task input. The candidate result serialization SHA-256 was `5c2699e993fd163a1a01c72c3905b46c8f364e329a8ddef47c37bb713952b936`.

Scope limitations: this does not establish automatic region selection, model usability, token savings, latency, GUI correctness, authority, or transfer. A formal container run and source/result manifest remain required before promotion.


## Corruption controls

An additive standard-library control checks four tampered fields and one truncated serialization. All four tampered inputs changed the SHA-256 digest and truncated JSON was rejected (`4/4`, `1/1`). This strengthens evidence-integrity coverage only; it does not change the 256-case candidate result or add any model/GUI/container claim.
