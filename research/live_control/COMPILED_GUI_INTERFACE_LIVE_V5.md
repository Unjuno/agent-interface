# Compiled GUI interface: fresh Chromium mechanics through caller v2

## Question

Can one model-grounded, bounded GUI interface perform two actions selected from
fresh intermediate evidence without another frontier-model generation, stop
before a missing second target, and retain the typed stop reason across the
shared adaptive caller?

The study uses an isolated Linux/X11 Chromium form with an independent POST
scorer.  Symbols are references only.  Every target action still passes a fresh
read check followed by ordinary pointer-target revalidation and admission.
The model contributes two points and a fixed method declaration; the caller
provides the method scaffold.  The changed case navigates the same surface to
`about:blank` after the first action.

## Preserved development sequence

All allocations were fresh, preregistered and run without retry.

| Version | Result | Information gained |
|---|---|---|
| v1 | failed before target input | The runtime permits at most one target-handle mint per program; both requested mints were batched. |
| v2 | failed before target input | A 24x14 patch wholly inside the form field was visually flat and correctly refused. |
| v3 | safe stop before target input | The read-only handle query returns `VALID`; the runner incorrectly required the later input-time status `REVALIDATED`. |
| v4 | live mechanics passed | Positive submitted successfully; changed stopped after one action.  Caller v1 collapsed nested `unknown_state` to `failed`. |
| v5 | live mechanics and typed composition passed | Caller v2 retained `unknown_state`, one completed action and confirmed partial delivery. |

The failed runs remain in `results/compiled-gui-interface-live-01` through
`-03`.  V4 and V5 remain separate evidence; no earlier runner or result was
overwritten.

## V5 result

The seed991025 changed case ran first, followed by the positive case.  Both
Luna-low calls returned field point `[180,243]` and submit point `[270,243]`,
inside the independently frozen boxes.  Schema preflight was a hash-pinned cache
hit and made no model call in this run.

The positive case entered exact `t991025`, observed 372 changed field pixels,
then selected Submit from the fresh predicates.  It observed the submission
page and the independent scorer read `{"value":["t991025"]}`.  The compiled
runtime made two transitions over three local observations with zero frontier-
model resumptions.  Both actions completed with verified release and separate
pointer admissions.

The changed case entered the token once, then the intervention replaced the
page with `about:blank`.  The next read-only check found no Submit target.  The
compiled runtime returned `SAFE_YIELD / unknown_state` after one completed
transition, no Submit target action occurred and the independent scorer remained
false.  Caller v2 returned:

```json
{
  "outcome": "EXECUTION_INCOMPLETE",
  "reason": "unknown_state",
  "delivery": "confirmed_partial",
  "execution_progress": {
    "status": "safe_yield",
    "reason": "unknown_state",
    "completed_actions": 1
  }
}
```

## Measured timing and usage

| Measure | Positive | Changed |
|---|---:|---:|
| Action to first useful feedback | 773.005ms, 568.488ms | 1,667.090ms |
| First action to independent semantic completion | 1,855.493ms | 4,871.539ms |
| Local compiled runtime | 2,280.368ms | 2,276.764ms |
| Grounding model process | 15,489.474ms | 20,102.124ms |
| Source observation to independent completion | 18,505.654ms | 26,118.139ms |
| Durable calls | 21 | 18 |

The two fresh grounding calls report 18,792 input tokens in total, of which
6,912 are reported cached input, plus 351 output and 121 reasoning-output
tokens.  Cached input is a subset of input tokens and is not added again.  Cost
is unavailable.

Windows and WSL audits verify preregistered source hashes, both unique model
call IDs, usage arithmetic, point boxes, raw frame hashes, releases, pointer
admissions, branch predicates, timing arithmetic, exact POST success and the
typed outer yield.  Manual image review confirms the filled field, submission
page and changed `about:blank` endpoint.

One accidental pre-preregistration invocation is recorded separately.  The
required result directory did not yet exist, so the runner could not pass its
first preregistration read and could not reach schema, model or GUI work.  The
formal run occurred once after preregistration.

The frozen v5 runner also retains the v4 text `live-chromium-seed991024` in the
opaque compiled `session_scope` label although the study and task seed are
991025.  Each case used a separate process and private handle registry, and this
study has no reuse path, so the mismatch does not join authority or state across
cases.  It is still a provenance-label defect and must be corrected in the next
runner rather than rewriting this frozen source.

## Decision and limits

The live mechanics and typed composition boundary advance to a matched
efficiency comparison.  This pair has no plain or current-optimized baseline.
It therefore provides no success rate, causal speedup, token saving, break-even,
portability or human-tempo claim.  The caller-authored method scaffold also does
not prove open-ended planner-authored interface synthesis.  The changed case's
field-pixel difference is confounded by the whole-page intervention; only the
absence of Submit input and independent submission is used as the safety result.
