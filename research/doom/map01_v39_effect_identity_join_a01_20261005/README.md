# V39 admission-to-release identity join A01

Disposition: **`PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT`**.

This experiment tests the next #59 gate from the 2026-10-05 intake comment: whether every admitted key in the retained V39/V15 fake-X closure can be matched to exactly one release receipt by program ID, step, intent token, owner ID, and key, while preserving the observed time order and refusing to infer task effects from XSync.

## Frozen inputs and run

- Current-main source closure: `88d875cc0916accb1a5fa36057253686f0586f1e`. The 11 source blob hashes are in `SOURCE_LOCK.json`; the independent auditor verifies each immutable Git blob at that exact commit. Before publication, all 11 hashes were rechecked unchanged at latest main `3bf3d49bec2aa26a9aaba38806f9e88296459356` (`BASE_REFRESH.json`).
- Raw event input: `RAW.json`, extracted unchanged from PR #7881 head `e02617b0d806dd05dd0cb24e44dbb4db2d393bd4`, path `research/doom/map01_v39_startup_release_order_a01_20261005/results/a03/RAW.json`; SHA-256 `93e7d1f56497c40efcd2b559aeb43c17ccda4f27b1545e3320a8f16c1dc9c4f6`.
- The retained trace has two admissions (F8, SPACE) and two release transitions (SPACE, F8). The join emits two unique identity pairs and validates admission ≤ release-call start ≤ owner KeyRelease start ≤ XSync return ≤ release-call return.
- Eleven host-Python standard-library tests pass. Twelve mutation cases cover missing/duplicate admission or release, wrong release key/step/token/owner, mismatched receipt key, authority overclaim, reversed timestamps, reordered key-up operations, and an inter-UP keymap query. Every mutation is classified HOLD or FAIL; none is a passing join.
- The independent raw-only auditor separately reconstructs both pairs and verifies all pinned source snapshots. Its first representation comparison failed; that initial output and repair note are preserved in `AUDIT_FIRST.stdout.txt` and `AUDIT_REPAIR_NOTE.md`. The corrected audit reports `PASS_RAW_JOIN_AUDIT_SCOPED`.

OrbStack was running, but `docker image ls` returned a daemon content-store read error (`operation not supported`). No container test was started or retried. The pure-Python test and auditor ran once on the macOS host; see `COMMAND.txt` and retained stdout files.

## H/T/D/C/U

- **H:** On this exact V39/V15 fake-X trace, admissions can be uniquely joined to per-key release receipts by all available identity fields and timestamp ordering; absent independent task-effect evidence stays HOLD.
- **T:** Replay the retained raw JSON with a small CPU-only join and an independent raw-only audit; inject ten identity/ordering faults and ensure none yields a pass.
- **D:** Identity subgate passes only with a unique one-to-one match and ordered brackets. Missing/ambiguous identity or receipt is HOLD; contradictory/reversed time is FAIL. Overall effect gate stays HOLD when independent effect rows are absent.
- **C:** Synthetic fake-X rows and event timestamps do not establish physical key state or causality; omitted fields may prevent the join from generalizing.
- **U:** This does not test live V39 startup, game/model, X11/OS input, application effect, latency, useful progress, threat response, bounded recovery, matched efficacy, or MAP01 completion. The raw has no independent task-effect row, so the full hypothesis is not passed.

No candidate, game, model, X server, or OS input was run. No new live allocation is granted or inferred.
