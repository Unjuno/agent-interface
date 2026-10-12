# V39 Executor V3 Active Cancel and Xvfb Key Release A01

## Scope

This is the next integration after the fake protocol peers exposed acceptance-order and control-stage mistakes. It uses the actual current-main Executor V3 class and the current V39 cancellation helper. Only its display backend is a focused test adapter; key input/release uses the actual Xvfb server and current InputOwner V4/V12.

## Pre-registration (H/T/D/C/U)

- **H:** A hard paired-health invalidation during an active pending planner turn cancels a production Executor V3 worker, verifies its actual Xvfb keyup before the stale planner answer can be admitted, and leaves final action admission rejected.
- **T:** One arm from retained seq2→seq3 values, source health/ammo 97/48 and synthetic current 80/48, with capture times rebased into the local monotonic clock and binding rebound to the focused Xvfb client. Executor V3 runs a bounded one-key hold through a test backend that delegates key effects and release to current-main InputOwner V4/V12. Current V39 monitor and cancel_invalidated_cover are AST-extracted. Record accepted-before-KeyPress, cancellation, terminal release, X events, planner result and final admission. One candidate invocation only.
- **D:** PASS_METHOD_SCOPED requires accepted_ns before X KeyPress, active key before observation, hard invalidation, matched executor cancel, cancelled terminal with verified release, independent keyup before planner wait returns, stale-answer rejection, stopped worker/owner and Xvfb exit 0. Any mismatch is STOP.
- **C:** Health drop is synthetic; backend is a test adapter, not production subprocess; planner is deterministic fake. Xvfb and owner operate real X-server input state. No semantic threat or task score.
- **U:** No live game, model, physical keyboard, semantic perception, production pipe/process failure, hard-kill recovery, or live MAP01 allocation. WSL2 Ubuntu substitutes unavailable Docker; no network namespace or hard resource caps.

Exact source/input hashes and the pinned environment are in FREEZE.json. Do not repeat this candidate after its single invocation.

## Result

**Formal status: STOP.** The frozen candidate ran once and exited 0 with `CANDIDATE_COMPLETE`, empty candidate errors, and clean Xvfb exit. The independent raw auditor is in `AUDITOR/audit_raw_a01.py`; its result is in `AUDITOR/audit.log.txt`. It independently confirms frozen source/input/candidate hashes and every other preregistered check, but the formal gate is not satisfied.

Executor V3 accepted at 21,192,058,510 ns; the observed X KeyPress was at 21,192,884,238 ns; the test reached the pending-turn observation with the key down. Health 97→80 then produced `HARD_INVALIDATED` (`below_hard_minimum`), the cancellation helper matched the active executor and requested cancellation, and Executor V3 returned `cancelled` with zero completed steps and a verified release receipt. The current InputOwner V4/V12 receipt records one explicit keyup attempt, XSync completion, and X-server keymap state up. However, the independent Xvfb KeyRelease event was at 21,198,543,189 ns, after the planner wait returned at 21,198,493,692 ns. Although the owner keyup receipt precedes planner return, the preregistered requirement was independent X confirmation before planner return. Therefore this arm is formally STOP. The planner answer was marked ineligible, final admission was `REJECTED_POLICY_INVALIDATED`, and the executor worker and input-owner thread stopped. Candidate and audit hashes are recorded alongside their logs.

This establishes only the bounded cancellation/release ordering for the current in-process Executor V3 class, current V39 health guard/cancel helper, current InputOwner V4/V12, and an Xvfb-backed test adapter. The health change and planner are synthetic. It does not establish production subprocess/pipe behavior, semantic perception or task success, hard-crash recovery, or live-game behavior.
