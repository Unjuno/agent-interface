# Integrated recovery surface key v1

Task: `INTEGRATED-RECOVERY-SURFACE-KEY-20260917-001`
Issue: #873
Publication BASE: `275480a47f8f06e119b3eb66709b96dbf735bd4b`

H: one X11 recovery identity key `{top_level_client_id, transient_for_or_null}` can cover both retained cross-app and same-app modal transitions without app-specific branches.

T: exact #855 and #864 evidence archives; readiness must first prove that every retained session contains all fields needed to construct the same key without inference. Only then may the preregistered 64-row validator matrix run.

D: if predecessor evidence lacks a required key component, retain `HOLD_PREDECESSOR_IDENTITY_INCOMPLETE` with formal rows/invocations 0 rather than mapping unknown to null. Otherwise proceed to the Issue #873 formal matrix.

C: missing schema fields can block a generalization even when each predecessor result is individually valid.

U: evidence-schema sufficiency only; no GUI/input/model execution and no claim about a universal cross-platform surface identifier.
