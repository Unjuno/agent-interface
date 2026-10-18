# A02 pre-freeze construction log

This file records design/construction checks only. These are not formal
candidate or auditor invocations and are not counted as assay results.

- Allocation: `8432-context-return-method-t0-a02-20261008`.
- Scope: deterministic finite method contract; no model, GUI, network, human,
  animal-learning, or product observations.
- Planned strata: 3 context paths × 2 cues × 3 history treatments = 18 rows;
  12 non-empty-history matched rows and 6 no-history rows.
- Implemented independent reconstruction checks: episode identity and count,
  context/cue/treatment labels, current mapping B, phase/order, eight-record
  support, cue/action balance, tagged-versus-untagged metadata, four test
  trials, outcome support, no-signal equality, and seeded-control separation.
- Six hostile construction mutations are expected to fail closed.
- An initial pre-freeze seeded-trace check failed because the authored return-A
  trace had only two repeated transitions while the continue-B trace had
  three. The fixture was corrected before any formal invocation: return-A is
  now a four-old-choice trace, continue-B alternates actions, and novel-C has
  one repeated transition. This is a disclosed design-stage correction, not a
  formal result or tuning of observed model data.
- A second preregistration-to-fixture review found the original draft omitted
  the Issue-required B-baseline test before the context-path test. Before
  freeze, the episode was revised to contain ordered four-trial B-baseline and
  path-specific phases, and the auditor now checks both exact phase identities
  and ordering. The phase-deletion mutant was redirected to this test sequence.
- Formal candidate/auditor invocations: 0/0; retries: 0.
- The A01 raw archive is not an input. Its result and byte-identity uncertainty
  remain unchanged.

The test log and exact source hashes will be completed after the pre-freeze
construction command. Formal freeze identity and one-shot outputs belong in the
run record, not in this pre-freeze log.
