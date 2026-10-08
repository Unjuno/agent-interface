# Real-app observe-only focus recovery transfer

Task `OBSERVE-ONLY-FOCUS-RECOVERY-INKSCAPE-TRANSFER-20260917-001`, Issue #855.

## Decision

**`PASS_REALAPP_OBSERVE_ONLY_FOCUS_RECOVERY_SCOPED`**

Source-first freeze commit: `0227cc737dee2ae5c5f92f5269ae1c904fe72d57` from immutable BASE `7f8376c8e74a581bd884416b5313ce4cda756b68`. Formal invocation 1, rows 8, reruns/replacements 0.

## First outcome

- source context resolves to real Inkscape **8/8**; admission-time current focus resolves to XTerm **8/8**; old A-bound action is rejected before task input as `focus_mismatch` **8/8**.
- `REPLAY_REJECTED_CONTEXT` returns stale Inkscape A **4/4** while actual focus remains XTerm B.
- `FRESH_OBSERVE_ONLY` returns current XTerm B **4/4**.
- actual focus remains XTerm before and after recovery **8/8**; recovery does not activate either application.
- every recovery receipt has `authority=none`, `task_input_granted=false`, `action_admission_eligible=false`; task-input API call count is **0**.
- keymap and pointer-button state are neutral before/after recovery **8/8**; SVG bytes unchanged **8/8**.
- fresh read-only recovery elapsed is descriptive only: median **0.688179 ms**, individual values 0.904356, 0.647027, 0.729331, 0.372012.

Frozen auditor: PASS, errors `[]`. Postformal frozen-source rehash 7/7 exact; copied-evidence corruption controls reject **4/4**.

## Interpretation

The #852 synthetic result transfers to one unmodified real desktop application: after stale Inkscape-bound authority is correctly rejected because focus moved to XTerm, a read-only X11 recovery query can report the actual current client/surface without moving focus, emitting task input, or granting authority. Replaying the rejected action context remains observably stale.

## Limits

One Inkscape 1.4 + XTerm + Openbox/Xvfb X11 fixture with authored setup focus transfer. This does not establish modal-state recovery, Calc transfer, UI-tree semantics, planner-boundary/token benefit, natural focus-loss frequency, target identity, or eventual corrected-action task success.
