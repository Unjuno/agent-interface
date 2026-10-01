# Integrated modal recovery surface binding v1
Task: INTEGRATED-MODAL-RECOVERY-SURFACE-BINDING-20260917-001
Issue: #865
BASE: 57fbc9fca01add6ef6be4ca2cf808bf234200fb4

H: same-app modal transition is invisible to app-class-only recovery identity but distinguishable with current top-level surface XID + transient relation.
T: exact retained #864 archive, 8 cases x stale/fresh receipt x app-class-only/surface-bound validator =32 rows, one formal invocation, reruns0.
D: coarse accepts stale8/8 and fresh8/8; surface-bound rejects stale8/8 and accepts fresh8/8; no-authority fields preserved; controls fail closed; audit/integrity pass.
C: this tests identity sufficiency, not semantic modal handling.
U: one Inkscape Save-As/X11 fixture and backend-specific XID/transient identity.
