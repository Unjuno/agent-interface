# Second MAP01 threat-fixture plan

V31 needs a live transfer test outside the exact v1 contact state. Repeating the
same fixture would measure another nondeterministic sample of a familiar state
and would not test transfer. This construction therefore chains one fixed,
model-free OS-input continuation from the hash-bound v1 fixture and preserves
its first outcome.

Session v8 permits a fixture to be loaded and a derived fixture to be saved in
the same setup-only process. The derived manifest retains parent manifest/save
hashes and parent/load tics. It does not change the v7 session or any hash-frozen
v28–v30 result. Loading and saving remain unavailable as action-selection tools.

The single frozen continuation is:

1. strafe left short;
2. retreat while firing short;
3. strafe right short;
4. coast 750 ms;
5. save and stop.

Every command uses the shared X11 Executor and semantic compiler. There are no
model calls, direct game action vectors, pauses, automap, labels, or hidden-state
queries for action selection. Linux tests cover the inherited hash/sibling/
exact-source checks and verify that optional parent metadata cannot bypass save
hash validation.

The exact command, source hashes, one-run cap, pass conditions, and failure
retention rule are frozen in `map01_threat_fixture_v2_prereg.json`. A candidate
passes only if its tic and frame differ from the parent, all programs release
empty, HUD health is exact, manual review shows a visible threat, and a fresh
process restores the same candidate tic from matching hashes. Failure is
retained without selecting a more favorable continuation.

This is fixture feasibility. It runs no v31 planner and supports no gameplay,
speed, token, reliability, or clear claim.
