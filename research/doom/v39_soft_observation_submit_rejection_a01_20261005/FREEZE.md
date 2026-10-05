# Soft-observation stale-submit boundary — A01 freeze

## H/T/D/C/U

**H.** In current integrated V39 initial admission, a non-invalidating observation can arrive after a cover submit uses an older expected sequence. The executor rejects the now-stale submit. The controller should retain the rejection as not admitted and proceed from the newly observed state, without converting this ordinary race into a session-aborting exception, cancellation, or planner start.

**T.** Source-extract the current branch's production `wait`, `submit_cover`, and initial admission gate. Feed exactly: submit at sequence 7, observation sequence 8 for which the validity monitor returns no invalidation, then an id-less stale-sequence rejection. Compare the retained pre-repair PR source with the candidate. Run the focused admission, controller, and source-refresh suites normally and with optimized Python.

**D.** Candidate passes this boundary only if the rejection is recorded with its original response, the decision uses sequence-8 image/evidence, no cover is recorded/admitted, no cancel/release wait is emitted, and no planner starts. Other admission and cancellation controls must remain green. Any unexpected event or accepted cover without its ID remains fail-closed.

**C.** A process-local deterministic FIFO and extracted Python functions may omit real executor scheduling, observation cadence, and application behavior. A stale rejection may be rare; this test establishes a concrete controller outcome, not frequency.

**U.** Synthetic controller construction only. No ViZDoom, model, GUI, X server, OS input, live allocation, latency, task effect, recovery efficacy, or MAP01 outcome is measured. The live lane remains unassigned.

## Frozen identities

- Fresh `main` at freeze: `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`.
- V39 controller and wait-test paths are byte-identical on main between PR #7904's declared base `2373e2c80f9385041c18b2df64405a6ffb7693ce` and freeze main `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`.
- Existing PR #7904 candidate before this change: `6f5503aa0e509a8252d12299a83965767a5d2ba8`.
- Pre-repair controller snapshot: `baseline_controller.py`, SHA-256 `0ced693d82ff38a80963adc54ff241e4d4abdbb3835d55a12856529c49c91e00`.
- Repaired controller snapshot: `candidate_controller.py`, SHA-256 `77ad1c74cb9071628d2329cee0049466b9e93e9117cbca568a2ed68240d7fdce`.
- Test source: `candidate_test.py`, SHA-256 `59ac0e3ff754b58bce6d405cf8ce4320b30a64905d1bf98203831d30e24e4f4f`.
- Runtime used for local construction checks: Windows 10, CPython 3.11.9.

The baseline source is the exact PR-head file at `6f5503aa0`; the candidate is the post-change file tested in this worktree. This is construction/regression testing and may be rerun as ordinary repair verification; it is not a consumed formal/live allocation.
