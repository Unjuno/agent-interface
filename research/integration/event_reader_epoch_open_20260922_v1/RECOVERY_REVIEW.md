# Recovery review: epoch/open binding allocation

This record accompanies the original `FREEZE.json` recovered from
`research/event-reader-epoch-open-20260922` (tip
`c686fdb34b83603c41d210389e1f1963105e0f8c`). The original branch contained
only that freeze file; its eight listed frozen source payloads and the formal
output are not present in the branch tree or current `main`. A bounded local
search under `/tmp` and `/Users/taka/Documents/Codex` found no saved raw
archive. The freeze records Git blob IDs and SHA-256 values, but the majority
of those Git objects are unavailable in this checkout, so those identities
could not be read back here.

## Reported result, not independently re-audited

Issue [#3937](https://github.com/Unjuno/agent-interface/issues/3937),
comment [5766218005](https://github.com/Unjuno/agent-interface/issues/3937#issuecomment-5766218005),
reports one completed 42-case formal orchestration and a raw-only audit with
zero errors and eight rejected corruption controls. It reports
`PASS_EPOCH_OPEN_BINDING_BOUNDARY_SCOPED` for the single-descriptor policy and
`FAIL_EPOCH_OPEN_RACE` for the sidecar-then-open policy. The reported raw file
is 276,789 bytes with SHA-256
`adb76a561eb3b4f273ced6b2ebede5c26a4a56eef874b518f91e784491018276`.

That raw file is not present in the recovered material, so its hash, audit,
counts, and outcome remain Issue-reported rather than independently verified
from bytes in this repository. The predecessor ZIP is likewise described by
Issue #3937 as local-only; it was not found and was not reconstructed. No
formal run, rerun, replacement, or tuning was performed during this recovery.

## Scope and follow-up

The Issue-reported outcome is bounded to unique-epoch replace-only schedules.
The same report says both policies fail the deliberately excluded in-place
rewrite and recycled-epoch controls; descriptor identity is not immutability
or epoch uniqueness. It makes no GUI, model/provider, action-input, ACK,
automatic cursor-reset, latest-state, or production-adoption claim.

Keep this freeze and the Issue's result comments as historical evidence. Do
not treat this note as a substitute for the missing raw bytes or as runtime
promotion. Any new experiment must be a separately scoped successor; do not
rerun the consumed allocation to recreate its claimed result.
