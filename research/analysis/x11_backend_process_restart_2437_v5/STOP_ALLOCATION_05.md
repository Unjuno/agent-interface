# Allocation 05 — stopped before formal freeze / launch

- Allocation proposal: `X11-BACKEND-RESTART-MULTICONTROL-2437-20261001-05`.
- Main observed: `dd1f9382ea20d15629516bb0dd995f4a4f1e4f32`; the preparation record is not a formal experiment freeze.
- Formal candidate invocation count: **0**. Raw auditor invocation count: **0**. Scientific PASS/FAIL: **none**.
- Disposition: `STOP_SHARED_CONTAINER_SLOT_UNASSIGNED_BEFORE_FORMAL_FREEZE`.
- GitHub coordination Issue [#5085](https://github.com/Unjuno/agent-interface/issues/5085) requires a named, exclusive Docker/OrbStack slot; its latest visible #5590 request at comment #5917534571 is request-only, not a grant. Current container ownership/inventory is unknown. No Docker context, image, or container was inspected, pulled, built, started, or changed in this allocation.
- The user's preference to use Docker Desktop is recorded. It does not override the repository's shared-lane arbitration protocol or authorize concurrent container use.
- Preparation only: 12 construction tests pass after transparent correction of both a missing schema in the test fixture and the candidate's old single-control output schema; private WSL Xvfb/Tk no-input preflight reported a 32-byte keymap and zero backend emissions. These are not Docker or formal-allocation results.
- Preserve proposal/H/T/D/C/U and script/source hashes in `PREPARATION_V5.md`. A future slot grant requires fresh main/owner/queue/inventory checks and a new formal freeze; this proposal is not resumable as-is. Never retry consumed Allocations 01–04.
- Previous Allocation 04 remains separately inconclusive (`STOP_INCONCLUSIVE_DISPATCH_STATE`); see `STOP_ALLOCATION_04.md`. No raw was reread.
