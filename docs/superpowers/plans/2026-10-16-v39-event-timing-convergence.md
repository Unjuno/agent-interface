# V39 event timing convergence

Goal: resolve open PR #8867 against current main without changing control policy,
removing current failure guards, or interpreting stage spans as isolated pipe latency.
Base: `5abbc37e7674d52ef452f08f64bce3b8cb82fd0b`.
Candidate: `598109fd6329ef88ec469557ae4beae2a2ef3002`.

- [x] Restore the candidate's two new timing tests; bind their AST harness to
  actual current duplicate-JSON/control-boundary guards. Run against main and
  preserve the missing-marker/missing-summary failures.
- [x] Transplant the producer marker, controller stage stamps, strict summary
  and explicit report contract. Preserve current duplicate rejection, failure
  cleanup, source refresh and authority gates. Update the two affected old test
  harnesses without removing guard execution.
- [x] Add a composed actual emitter→serialized row→actual reader/wait→monitor
  check, monitor-exception final timestamp, malformed/duplicate JSON refusal,
  current control failure refusal, and missing/reversed/bool timestamp cases.
  Keep raw log rows and stdout-enriched rows distinct in saved evidence.
- [x] Run relevant controller/emitter/retirement tests in normal and optimized
  Python. Preserve source pins, rows, first failures, driver and limits; verify
  saved records separately without starting a game, model, WSLc or native input.
- [ ] Review current exact head/base and local checks, integrate by conditional
  forward main update under actual protection rules, then close #8867 with the
  successor and unchanged #59 scientific boundary. Refresh the work map and
  remove only this worker's proven-preserved integration refs.

No performance improvement is claimed. The stdout marker precedes serialization
and write; enqueue precedes the queue operation. Each interval contains its named
stage overhead and scheduling. Child/parent clock comparability is a same-host
assumption, not evidence for remote hosts. No actual environment response, input
release, controller death, task effect or matched economics is qualified here.
