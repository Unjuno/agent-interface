# Result — cross-domain retained-evidence handback T1

**Disposition: `PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED`.** The frozen
candidate ran once in WSL and exited 0. The independent raw-only auditor ran
once in a separate Windows Python process and exited 0. Retries: 0. Audit:
10/10 checks, no failures. Candidate, audit and freeze SHA-256 values are in
`RESULT_HASHES.json`.

## Observed transfer

Four provenance-bound records preserved the differences between two retained
domains:

- MAP01 v38's first exact plan frame and the three v39 first exact plan frames
  remain `OBSERVED_CHANGE`, `semantic_task_feedback=unverified`, and
  `task_effect=UNRESOLVED`. V39's independent score of one kill remains
  domain progress; `map_exit=false`, so this is not task completion.
- The v39 health-revocation record remains a separate verified
  `PHYSICAL_RELEASE`; the three same-source event intervals are retained only
  within that source event. They are not generalized to actual held-key
  duration, task effect, or other clocks.
- Browser comparison04 direct task-6 retains its independently recorded
  exact-once server submission as `TASK_EFFECT`, while the visual
  acknowledgement stays `UNKNOWN_NOT_OBSERVED`. Save and close release
  evidence remains separate from submission success.

The independent audit rechecked six retained artifact SHA-256 values and each
Git blob against the pinned main tree. Six mutation classes were rejected:
viewport change→task effect; release→task effect; invented visual
acknowledgement; forged source digest; cross-source clock join; authority
expansion. The test suite passed 8/8 before the frozen pair; the workspace
index check passed with 152 top-level directories reachable at the frozen
base. The public six-task verifier separately passed its scoped correctness
audit over all 1,051 archived members while retaining
`HOLD_INTEGRATION_INCOMPLETE`.

## Interpretation and limits

This is a retained-source representation candidate only. It does **not** meet
open Issue #2221's live/model recovery acceptance: no model selected
DONE/WAIT/QUERY_EFFECT/RETRY/ABORT, no live route or independent new scorer was
run, and no task value, held-out transfer, latency/cost, useful DOOM feedback,
MAP01 clear, or product result is established. Exact server submission does
not establish that its visual acknowledgement was rendered or seen. The
closed #1530 `HOLD_DISTINCT_EFFECT_TYPES_REQUIRED` and #2221 v1
`HOLD_PRE_MODEL_HAND_BACK_TRANSFER` remain immutable.

Docker Desktop's Engine was stopped. This experiment is a small standard-
library CPU analysis, so it ran across WSL/Windows processes without starting
Docker or claiming container evidence. No model, GUI, OS input, or network task
call occurred. The outstanding next discriminator remains a separately
authorized live/model cross-domain recovery block with independent domain
scorers; this PASS is not a reason to close #2221 or Issue #59.
