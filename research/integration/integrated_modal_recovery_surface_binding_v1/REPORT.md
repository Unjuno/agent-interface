# Integrated modal recovery surface binding v1 — result

Decision: **PASS_MODAL_SURFACE_BINDING_REQUIRED_SCOPED**.

Exact merged #864 evidence was replayed from Git blob `bcf8203d54907cea5676d8143783dd249e6dda3c` / SHA-256 `5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6`. Eight retained same-app Inkscape main→Save-As modal sessions each had the same application identity but a distinct current top-level surface and `WM_TRANSIENT_FOR` link back to the source main surface.

Formal first outcome: 32 deterministic rows, one invocation, reruns 0. `app_class_only` accepted stale-main 8/8 and fresh-modal 8/8. `surface_bound` rejected stale-main 8/8 as `surface_mismatch` and accepted fresh-modal 8/8. All accepted receipts remained observation-only (`authority=none`, task input false, admission false). Independent audit errors were empty. Frozen sources rehashed exactly after formal and five copied-evidence corruptions were rejected 5/5.

Interpretation: application identity is insufficient as the recovery **surface dependency** when focus moves between same-app top-level/transient surfaces. A backend-visible current surface identity is required to avoid treating stale main-window context as current modal context. This does not establish a universal cross-platform semantic surface identifier, automatic modal handling, corrected-action success, planner/token benefit, or production promotion.

GitHub result publication retains the exact 31,811-byte `formal_rows.json` losslessly as `formal_rows.json.xz`; the raw JSON and compressed archive digests are recorded in `POSTFORMAL.json`.
