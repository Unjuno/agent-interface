# #7165 A02 — current-context invalidation and fallback

## H / T / D / C / U

- **H:** A remembered discrimination requirement is safe only as a request for
  fresh evidence. It may select a targeted observation when the requirement is
  complete, source-bound, and tied to the current context generation. Missing,
  contradictory, stale, or otherwise unjoinable cues must trigger ordinary
  full revalidation. It never grants identity or action authority.
- **T:** Exhaustively enumerate a finite two-cue contract with cue states
  `A`, `B`, `MISSING`, `STALE`, and `WRONG_SOURCE`; requirement completeness,
  provenance validity, and context-generation agreement; and independently
  specified current full-revalidation observations. Compare the memory-gated
  path against always-fresh full revalidation. Run the candidate once and a
  separate raw-only auditor once. This is an analytical contract experiment;
  no OS, GUI, runtime, model, or timing behavior is in the claim.
- **D:** `PASS_METHOD_SCOPED` only if every enumerated candidate decision equals
  the independent full-revalidation oracle, no stale/missing/conflicting input
  is bound, every invalid/incomplete memory requirement takes fallback, and
  all corruption controls are rejected. Otherwise preserve the first `FAIL`.
  Even on PASS, memory promotion is refused unless the candidate reduces
  fresh observation work relative to an identical explicit fresh-cue request;
  this experiment does not measure model-boundary or user-task cost.
- **C:** Ordinary fresh revalidation may already ask for the same cues and
  achieve the same result at the same cost. Context-generation metadata may
  itself be incomplete or dishonest; the model does not establish native
  source authenticity or detect arbitrary writers that forge current labels.
- **U:** The model assumes the tagged generation/source fields faithfully
  describe each observation and that the current full-revalidation oracle is
  an authoritative fixture oracle. Results do not authenticate application
  identity, establish real context invalidation, prove GUI behavior, or show a
  memory-specific efficiency benefit.

## Frozen identity

- Issue: [#7165](https://github.com/Unjuno/agent-interface/issues/7165)
- Allocation: `DISCRIMINATOR-CONTEXT-7165-A02-20261009-01`
- Base: `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`
- Branch: `research/7165-discriminator-a02-20261009`
- Output: `research/observation/native_discriminator_7165_a02_20261009/`
- Formal candidate and auditor each run at most once after freeze.
