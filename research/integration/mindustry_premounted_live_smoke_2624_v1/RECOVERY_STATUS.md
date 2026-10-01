# Recovery status: original allocation retained as infrastructure STOP

This package preserves the exact four frozen source/preregistration files from
`research/mindustry-premounted-live-smoke-2624-20260926` at
`68544c4db43ce3d55b3553e17223165cf2074816`. The historical source commits are
retained as ancestry of the recovery merge; no frozen file is rewritten.

## Recorded outcome and evidence boundary

The allocation `mindustry-premounted-live-smoke-2624-20260926-01` was frozen at
0/1 formal sessions, then invoked exactly once. The issue's first-outcome record
reports `STOP_INFRASTRUCTURE` at `RuntimeError('Xvfb not connectable')`, before
Openbox or Java/Mindustry launch. Exact assets passed identity checks, no
controller/task-input/model/provider calls occurred, and the owned Xvfb process
and socket were cleaned up. This is an execution/setup STOP, not a fixture
startup failure or scientific negative result. The allocation must not be
retried.

The pre-formal freeze and first-outcome records are preserved in [Issue #2624
comment 5841725567](https://github.com/Unjuno/agent-interface/issues/2624#issuecomment-5841725567)
and [Issue #2624 comment
5841739874](https://github.com/Unjuno/agent-interface/issues/2624#issuecomment-5841739874).
The frozen branch readback identities are: preregistration
`50b010d0b869b5a8664e00bd2705ee80a5d2bd8e`, auditor
`9fbe1c6e16eeb7479e705d6fe58988da19a76ed3`, study
`f637d304a4cde60dde4293c3f397ef325a28e727`, and tests
`db83557cce793f03cf9b34acd10d9eced71e4e2b`.

The issue comment records SHA-256 values for `RESULT.json` and the asset
manifest, but those raw files are not present in the source branch. This
recovery therefore preserves the exact frozen source and the bounded
issue-reported STOP; it does not independently re-audit the terminal raw result
or claim a scientific PASS/FAIL.

The separate #4454/#4457 follow-up allocations and their outcomes remain
distinct. In particular, do not replace this STOP with a successor's outcome,
pool partial evidence, or run the consumed allocation again.

## Verification for this recovery

- The four files' Git blob IDs match the frozen source branch exactly.
- The source branch changes only these four additive paths relative to its
  intake base; no unrelated code or active branch changes are included.
- The four frozen unit tests passed (4/4) in network-disabled container image
  `agent-interface-r3-batches:20260927-03`
  (`sha256:cb4e745a49e0ed05f6138d8608d9337028f30cd244c60f13063891782235f466`).
- Python syntax and preregistration JSON parsing passed in the pinned Python
  3.13.5 container. Repository-wide `git diff --check` flags one trailing
  space in the original frozen `audit.py`; it is retained unchanged to preserve
  the recorded source blob.
- No formal Mindustry session or fixture acquisition was run for this recovery.

Disposition: `STOP_INFRASTRUCTURE` (historical report); raw-result
reproducibility remains limited because the retained raw payload is unavailable.
