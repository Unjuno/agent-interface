# Issue #8432 — T0 A02 preregistration

## Why A02

A01 is preserved as `FAIL_METHOD_GATE`: its raw contains 9 episodes (3 context
paths × 3 history treatments), while its auditor expected 12 matched episodes;
its candidate summary also reported 18. The committed A01 raw has a separate
byte-identity discrepancy. A02 is a new allocation and new additive path. It
does not repair, overwrite, re-audit, or use A01 raw. The only question here is
whether the corrected finite assay has a coherent independently auditable
denominator and scorer contract.

## H / T / D / C / U

**H.** A corrected deterministic context-return assay can materialize three
context paths × two cue-identity strata × three history conditions as exactly
18 episodes, including exactly 12 matched non-empty-history episodes and six
no-history controls; all retain equal source support and B as the current test
mapping. An independent raw-only audit will reconstruct each episode and
reject count/support/context mutations. This does not test renewal in a model.

**T0.** Materialize A-acquisition/B-correction/B-test/path-test sequences for each of
`return_A`, `continue_B`, and `novel_C`, crossed with `cue_x` and `cue_y`, and
with `chronological`, `context_tagged`, and `none` history treatments. Each
episode has an ordered four-trial `test_B_baseline` followed by a four-trial
return-A, continued-B, or novel-C phase. The two non-empty treatments share the same eight source-bound A/B examples; the tagged
condition adds applicability metadata only. All test episodes retain mapping
B, two cues, two actions, four trials per test phase, and identical scorer
support. A separate auditor re-derives the complete Cartesian denominator,
records, test phases and synthetic scoring controls from the frozen fixture.
Run candidate and auditor once each in separate pinned network-disabled
OrbStack containers. No model, GUI, game, network, or OS input.

**D.** `PASS_METHOD_SCOPED` only if the auditor reconstructs all 18 episodes,
12 matched-history episodes and six no-history controls; every episode has
eight records when history is present (zero otherwise), identical cue/action
support, current mapping B and four test trials; the no-signal scorer control
is equal across contexts; the authored seeded trace has greater recurrence and
regret on return-A than B/C controls; all six frozen mutations are rejected;
and candidate/auditor invocations are exactly 1/1 with zero retries. Any count,
support, identity or mutation failure is `FAIL_METHOD_GATE`; an environment or
provenance gate failure is STOP, with no host fallback. A method PASS is not
behavioral evidence.

**C.** A matched deterministic fixture may still encode the expected signal by
construction; context tags can change prompt length or prime a model; the
synthetic scorer does not show that an LLM learned, corrected, or renewed any
association. A01 already establishes that count assertions can contradict
materialized rows.

**U.** Whether a fixed model shows A→B→A renewal, whether a context-tagged
ledger changes proposal recurrence, and any GUI, human-learning, effect,
safety, deployment or product outcome remain untested. The A01 raw archive
identity remains unresolved and is not repaired here.

## Frozen decision rules

- Episode denominator: 3 context paths × 2 cue strata × 3 history treatments
  = 18 total.
- Matched histories: 3 × 2 × 2 non-empty history treatments = 12.
- No-history controls: 3 × 2 = 6.
- History support: 8 source records per non-empty history episode; none arm has
zero. All treatments use the same two cues and action support.
- Test support: ordered four-trial `test_B_baseline` followed by an ordered
  four-trial return-A/continued-B/novel-C phase, with current mapping B in
  every episode.
- Diagnostic traces are authored deterministic code-path controls only. They
  are not sampled model outputs and cannot produce an A01/A02 renewal claim.
- Candidate and auditor formal invocations: one each, no retry. Construction
  tests are not formal invocations.
