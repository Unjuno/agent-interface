# V39 Visual-Changed Active-Hold Xvfb A01

## Question and scope

On the retained current-main V39 signal-pair monitor, does a new typed observation with the same health (97), ammo (48), and pointer binding but a different RGB frame identity invalidate a pending model turn while a real Xvfb-owned key is held? Does owner close release that key?

This is a component-boundary experiment. It is not a live game, physical keyboard, model, semantic threat, or task-effect test.

## Pre-registration (H/T/D/C/U)

- **H:** A changed frame identity with unchanged monitored health/ammo may leave cover valid and the pending answer eligible, while actual input remains held until explicitly closed.
- **T:** A changed-frame case and same-frame control. Each starts current-main InputOwner V4/V12 against Xvfb, sends XTest keydown to a focused X client, delivers retained sequence 3 during `PersistentPlannerAdapter.await_turn`, records monitor/admission outcomes and X-server key state, then closes the owner and independently observes keyup. One candidate invocation only.
- **D:** Intended method pass requires two complete arms, unchanged input/owner observations, answer/admission state, and clean owner/Xvfb teardown. STOP on fixture/runtime/cleanup failure. Semantic threat detection is outside the claim.
- **C:** RGB difference need not mean action-relevant semantic change. Health/ammo guards cover only their authored predicates. Xvfb keymap proves X-server state, not application receipt or physical keyboard state. A deterministic fake client is not a model.
- **U:** No semantic labels, game effect, physical device, production async observation callback, competing input transport, or live allocation. Docker Desktop was unavailable, so this run used WSL2 Ubuntu 24.04.3 and its installed Xvfb; no hard resource cap was enforced.

The machine-readable freeze and exact source/input SHA-256 values are in `FREEZE.json`.

## Execution and raw evidence

Candidate command:

```text
cd /mnt/d/codex-research/worktrees/v39-visual-active-hold-xvfb-a01-20261012/research/doom/v39_visual_active_hold_xvfb_a01_20261012/SOURCE
PYTHONDONTWRITEBYTECODE=1 /tmp/v39-visual-hold-venv/bin/python -B candidate.py --out ../results/A01 --display :132
```

Environment: CPython 3.12.3, python-xlib 0.33, six 1.17.0, Xvfb `2:21.1.12-1ubuntu1.8`, WSL2 kernel `6.18.40.1-microsoft-standard-WSL2`. Docker daemon was unavailable. The first preflight invocation stopped before candidate start because the venv had not yet been created; it produced no result leaf. The single candidate invocation occurred after environment preparation and wrote `results/A01/RAW.json`.

Raw SHA-256: `3fbd2c2588b13d3ca22543db7a70cb433bcd6faf415188077f3e6ac4e96cae0f`.

The raw records both arms with no runtime errors. In both, Xvfb observed keydown before and during the pending turn and after the planner answer. The changed-frame arm had `monitor_invalidation: null`, `answer_eligible: true`, `final_status: READY_FOR_FRESH_EXECUTOR_ADMISSION`, and `executor_admission: null`. Health and ammo guard outcomes were both `UNCHANGED`. Owner close produced a verified X-server keyup receipt, independent observer saw keyup, owner thread stopped, and Xvfb exited with code 0. Same-frame control matched these policy and key lifecycle outcomes.

## Result classification

**Formal A01 status: STOP.** The candidate program returned exit code 1 and wrote status STOP because its final condition treats any nonempty `cleanup` dictionary as failure, while normal cleanup records `{"xvfb_exit": 0}`. Thus the run did not satisfy the preregistered candidate exit criterion. Preserve that status; do not overwrite or rerun A01.

The captured component observations are still interpretable: this V39 monitor only compares RGB frame identity to reject disagreement on a duplicate same-sequence cross-transport observation. For a new advancing sequence, a changed RGB hash by itself did not invalidate the health/ammo policy. The fake planner answer remained eligible. The result also demonstrates the existing owner's ability to release this isolated X-server key on close. It does not establish that RGB change should invalidate a policy, detect a threat, interrupt a real model, stop an active executor, or improve task outcome.

## Audit boundary and next useful test

A raw-only audit should verify source/input hashes, both arms, transition and owner receipts, independent keyup, stopped thread, Xvfb exit, and classify the candidate exit/status bug as a harness defect. No formal rerun is authorized by this record. The next science should test a semantic or explicitly authored visual policy event through the production observation-to-cancel path while an action is active, with real task feedback and bounded recovery; it should not simply repeat RGB-hash-only input.

Raw-only audit result: PASS_RAW_CONSISTENCY; formal A01 status remains STOP. The audit confirms all frozen hashes and both Xvfb owner-close keyup observations. LOCAL_VERIFICATION.md records the 61/61 focused current-main regression result. The audit file SHA-256 is 909e93bc07fa9521ec71e8a69203edb85ba40887d83c8ccdb2ed6a060a2b425e.

Network environment wording is corrected by FREEZE_ERRATA.md; original preregistration bytes remain unchanged. No network namespace isolation was active during candidate execution.
