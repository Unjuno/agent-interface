# Existing patch servo with interruption cause and cooperative wake

`cause_servo_session_v1.py` composes the existing session_v21/patch_servo_v5 policy
and guided continuation implementation with owner10 initialization. Its matching
entrypoint uses executor_v5/lease_cause_v2. No patch tracker, correction policy,
continuation rules or default entrypoint was replaced. This integrates prior
[servo research](SERVO_INTERFACE.md) with the recent cause/wake work rather than
introducing another task-specific visual controller.

## Actual assistant use

One fresh Inkscape seed-215 episode used the private socket bridge. The assistant
viewed the initial original image and selected the patch [592,369,56,44], initial
pointer path (618,391)→(628,391), target displacement [20,0], and at most three
corrections. The unchanged local patch policy reported zero initial displacement,
issued one guarded continuation to (648,391), then reported [20,0] and local goal
reached. The assistant inspected the feedback/continuation records and final image,
issued a separate save, reviewed its image and input-state detail, and finished.

The saved SVG independently passes x=66.94915 against the declared 66.95 +/-1,
y=50, width=40, height=30, no transform. Both terminals have no interruption.
This is a familiar single-object layout, not held-out perception or distractor
coverage. The assistant chooses the target patch and program; intermediate replies
come from the existing bounded local controller, not model inference while held.

Acceptance to servo terminal was **902.056683 ms**, excluding model planning,
socket clock exchange, save and scoring. Initial capture to independent evaluation
was **66.983065935 seconds**, including inspection, commentary and detail retrieval.
Six socket exchanges delivered 39 events; eight exact frames were reconstructed.
No ratio against previous different tasks is claimed.

## Actual focus fault at a servo yield

One separate scripted fresh app session blocked output at pointer_yield before
policy evaluation. A private X connection verified Button1 down, moved focus and
verified release while output remained blocked. After restoring focus and resuming
output, the terminal returned needs_decision with zero completed steps and the
original verified focus_changed cause. No servo_feedback calculation or continuation
was emitted after release. A fresh observe-only intent then completed without an
inherited cause. This is a controlled callback stall, not a real network or capture
stall. It does not establish feedback latency while arbitrary code is blocked.

## Presentation issue retained

The compact receipt raised 15 attention entries for servo and four for save. Some
are appropriate unknown-schema review requests: bracketed input state, continuation,
yield and servo outcome have not been given typed compact presentation. Others
incorrectly call numeric tracking.error values (matching distance) nested exception
evidence. The assistant read the relevant records; no full-report model receipt
or complete review of every nested field is claimed.

Next add a typed presentation for these existing servo records that distinguishes
tracking metrics from exceptions while retaining lost/ambiguous/expired outcomes,
unverified release, identity/revision mismatch and genuinely unknown fields. Test
on preserved successful and interrupted reports, then self-use. Do not suppress
all fields named error or treat no attention as task success. Further robustness
tests should reuse the existing distractor/occlusion cases rather than repeat only
this familiar rectangle.

## Evidence and limits

`results/cause-servo-live-01/` stores the original reports, receipts, source pins,
strict score, SVG and exact frames. `results/cause-servo-focus-01/` stores fault
events, owner records, three frames and cleanup returns. `audit_cause_servo_v1.py`
checks source hashes, raw socket slices, receipt reconstruction, all eleven frames,
independent geometry and fault cause/no-continuation behavior. The live bridge
handle and fault process each exited 0; no independent per-child cleanup inventory
is claimed. Source manifests are not exhaustive environment manifests. Model
identity, receipt time, actual tokens/cost, general speed and Research Freeze remain
unverified. Historical experimental files and defaults are unchanged.
