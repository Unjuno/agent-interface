# Readiness private-fixture Rung1 — first outcome

Decision: `PASS_READINESS_PRIVATE_FIXTURE_TRANSFER_SCOPED`.

One source-first formal invocation; reruns0. Parent #1197 vocabulary/recovery mapping is unchanged. The only promoted factor is evidence acquisition/classification.

## Semantic fuzz
- cases: 4,000; probes: 8,000
- evidence-readiness candidate/oracle mismatch: 0
- pixel-only baseline state/recovery errors: **7,000/8,000**
- intentionally stale probes: 400; stale READY promotions: 0
- startup-failure/target-unavailable collapse: 0
- modal errors: 0; UNKNOWN errors: 0
- authority promotions: 0

## Real private-X11 transfer
- fresh Xvfb/Tk cases: **64**; probes: **128**
- evidence-readiness candidate/oracle mismatch: **0**
- pixel-only baseline errors: **112/128**
- authority promotions: 0
- clean fixture/Xvfb cleanup: **64/64**

This closes the controlled transfer from typed readiness semantics to actual process/window/event acquisition. It does not prove production readiness detection: the fixture exposes structured signals that Calc/XTerm/games may not expose directly. Pixel-only baseline is deliberately constrained by the parent safety rule that pixels cannot establish READY_FOR_ACTION, so its error rate is a representation/evidence-availability result, not a claim about model vision quality.

Next valid rung is transfer of the same frozen eight-state classifier to at least two real application fixtures while keeping recovery/authority semantics unchanged.

Integrity: source archive SHA-256 `f27a6fc5fb049b0a0f029f6ab90e4cfc57e9fd7d529c395cfd75f870059a8324`; RESULT SHA-256 `98b4eadb4bd84f57ae125bf652002de797ca2a1967478381a9f4609458c59c72`; semantic ledger gzip SHA-256 `ccb50d15f21672b03c7bca1f0f98d0c12ead36fdf92c1f38e68287485ac934f7`; audit PASS/errors[]; source rehash exact; corruption controls5/5 reject.
