# V39 Active Invalidation to Xvfb Key Release A01

## Scope

This new experiment tests the previously untested link between a real typed paired-signal invalidation, current-main cancel-before-planner-interrupt logic, an owner-held Xvfb key, and stale planner answer rejection. It is distinct from the visual-hash-only A01.

## Pre-registration (H/T/D/C/U)

- **H:** Health below the authored hard minimum during a pending turn triggers authority reduction. The production helper cancels the active cover before planner interruption; owner-thread keyup is verified before turn completion, and the later completed answer is ineligible.
- **T:** Two isolated arms: source 97 to current 80 (hard minimum 89) and a 97 unchanged control. Both use retained typed seq2→seq3 structure/binding and exact current-main source. A real Xvfb owner holds key a. A minimal protocol peer connects cancel_invalidated_cover to InputOwner V4/V12 up_batch. One invocation per experiment; no game/model/physical input.
- **D:** PASS_METHOD_SCOPED requires invalidation, exact cancel-before-interrupt ordering, actual Xvfb keyup before the planner completion return, ineligible answer, final policy rejection with no executor admission, unchanged control, and clean teardown. Otherwise STOP.
- **C:** The health drop is synthetic. The executor peer is a minimal protocol double, though it invokes the current owner API and observes the actual X server. The model is deterministic fake output. No semantic vision or task result is tested.
- **U:** No live game, production executor subprocess, physical keyboard, semantic threat, scheduling stress, or hard resource limits. WSL2 Ubuntu is used because Docker Desktop is unavailable. Network is not isolated; candidate code uses only local files, Python modules, and Xvfb.

Exact sources, retained inputs, hashes, environment, and full conditions are in FREEZE.json.
## A01 execution and result

The one frozen WSL2 Ubuntu 24.04.3 candidate invocation used CPython 3.12.3, python-xlib 0.33-2, Xvfb 2:21.1.12-1ubuntu1.8, display :133. Docker was unavailable and no network namespace was configured; candidate code uses only local files, Python modules and Xvfb.

The synthetic hard-drop arm (health 97 to 80; hard minimum 89) produced health:below_hard_minimum. Production cancel_invalidated_cover wrote and flushed the executor cancel before calling planner interrupt. The executor protocol peer called current-main InputOwner V4/V12 up_batch; its joined owner receipt reported X-server keyup verified. An independent Xvfb observer received KeyRelease and observed keyup before the planner wait returned. The completed answer was ineligible with cancellation requested, and final admission was REJECTED_POLICY_INVALIDATED with no Executor admission.

The unchanged control did not cancel, kept the key down during the pending turn, and preserved planner-answer eligibility. The final admission result was READY_FOR_ACTION_VALIDITY, because current V2 intentionally inserts a fresh action-validity stage before the later executor-ready state. The preregistered candidate incorrectly required the later state without invoking that stage, so its control assertion failed. **Formal A01 status: STOP.** Do not relabel this as PASS or rerun the same experiment. This is a useful observed handoff requirement for the next integration.

Candidate exit was 1; Xvfb exited 0 and both arms were recorded. The full original raw is results/A01/RAW.json (SHA-256 70971e914edae31af0b3e0cd8b1316410daff6d9d3e28b42b949a4adfd0b1837). The final raw-only audit is PASS_RAW_CONSISTENCY (SHA-256 f9022cc31cef43f46538de557181849a52fef01752938a5f20715ce29e6abf97) and explicitly preserves the formal STOP.

An initial auditor version was mistakenly placed inside frozen SOURCE and therefore changed a frozen source hash. Its output is preserved as results/A01/AUDIT-preaudit-path-error.json; the corrected auditor now lives outside SOURCE at AUDITOR/audit_raw_a01.py. Candidate was not rerun and FREEZE.json remains unchanged.

## Interpretation

This component test establishes that the current-main cancellation helper and owner stack can deliver a server-observed keyup before a pending completed answer becomes eligible when the guard sees a hard health invalidation. It does not establish live game threat recognition, production executor subprocess behavior, physical input state, task feedback, recovery quality, or task completion.

## Next test

Use the exact READY_FOR_ACTION_VALIDITY control path through fresh action-validity evaluation and accepted Executor admission, and in the invalidation arm include a production Executor process or a protocol-faithful isolated substitute with hard-crash/failed-up cases. Only after those local integration gates should the still-unassigned #59 live gameplay allocation be sought.
