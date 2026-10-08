# Same-app modal observe-only focus recovery — Inkscape

Task `OBSERVE-ONLY-MODAL-SURFACE-RECOVERY-INKSCAPE-20260917-001`, Issue #861.

## Decision

**`PASS_SAMEAPP_MODAL_OBSERVE_ONLY_RECOVERY_SCOPED`**

Source-first freeze commit is recorded in Issue #861. Formal invocation 1, eight fresh first sessions, reruns/replacements 0. Frozen auditor returns PASS with no errors.

## First outcome

- source focused top-level is Inkscape main **8/8**;
- after setup-only `Ctrl+Shift+S`, admission-time focused top-level is a distinct Inkscape transient **8/8**, same app class, with `WM_TRANSIENT_FOR=source main` **8/8**;
- old main-surface-bound hypothetical action rejects before task input as `focus_surface_mismatch` **8/8**;
- replay policy reports stale main surface **4/4** while actual focus remains modal;
- fresh observe-only policy reports exact current modal surface and transient relation **4/4**;
- recovery preserves actual modal focus before/after **8/8**;
- every receipt has authority `none`, task-input false, admission-eligible false; task/recovery input API calls **0**;
- setup chord is fully released before admission; keymap/button state neutral through recovery **8/8**;
- SVG bytes unchanged **8/8**.

Fresh read-only recovery elapsed time is descriptive only: median **0.641103 ms** over four candidate rows.

## Integrity

Postformal frozen-source rehash 7/7 exact. Four copied-evidence corruptions are rejected 4/4.

## Interpretation

A coarse application identity is insufficient for focus recovery: main document and Save-As modal are both Inkscape, but current authority context has changed to a distinct transient top-level surface. A fresh read-only X11 recovery receipt can expose that current surface/transient relation without moving focus, emitting task input, or granting authority. Replaying the rejected main-surface context remains stale.

## Limits

One Inkscape 1.4 Save-As dialog on X11/Openbox/Xvfb and one authored setup shortcut. No arbitrary modal/UI-tree semantics, semantic control identity, natural occurrence rate, planner/token benefit, corrected-action success, or cross-platform claim.
