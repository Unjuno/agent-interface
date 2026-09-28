# Issue #2447 — single-sequence construction result

Decision: **PASS_CONSTRUCTION / Issue #2447 remains HOLD**. This validates that one additive runner can execute three sequential bounded subgoals in one Docker/X11 episode and preserve evidence. It does not satisfy the Issue acceptance criteria or consume a formal allocation.

## Case and measured outcome

- Case: `issue2447-construction-2447005`; seed 2447005; MAP01 sector-165 drop; temporal gate; requested held-out setup heading 95°.
- Docker Desktop image: `agent-interface-map01-lab:2447-preflight-20260927`, `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`; runtime network disabled.
- Scorer setup: sector 165, Z=-64, actual heading 91.406° (error 3.594°, within frozen <8° setup tolerance).
- Subgoal 1 (forward/drop phase): optical-flow temporal gate independently recomputed from saved PNGs as `DROP_COMPLETED`; endpoint-only metric was `NO_DROP`; no redundant extra-forward action issued. Scorer-only postcondition was sector 38, Z=-128 from sector165/Z=-64.
- Subgoal 2 (Right 190ms): a fresh screenshot was hashed and bound to matching focus/surface/geometry; independent scorer recomputed yaw change -15.8203°.
- Subgoal 3 (Left 190ms): a second fresh bound screenshot; independent scorer recomputed yaw change +15.8203°.
- Releases: setup and controller releases verified empty; all recorded releases had no keys/buttons down.
- Controller-visible decision evidence remained X11 pixels and public focus/surface/geometry. Hidden sector/Z/angle were used only by the episode scorer and independent audit.

This is one seed, one sequence, one temporal arm. It does not show comparative benefit, a false-positive rate, sequence transfer or a safety distribution.

## Audit and retained failures

- Final independent audit: `audit_v5.py`, SHA-256 `cc02facc0f313f883a4ff26e893b91aff29319658dfaf32570ae323c21ba3d77`; errors=[].
- Earlier audit failures are retained, not overwritten: v1 stopped on an auditor NameError; v2 miscompared the observation binding; v3/v4 passed progressively narrower checks before v5 added currentness ordering and setup alignment.
- Raw run artifacts: 33 files / 1,779,676 bytes under `raw/`, individually SHA-256 indexed. The artifact includes all 12 temporal-phase frames, both handoff screenshots, action/event/release logs, controller context and scorer result.
- No formal rows and no retries. This construction run is not counted as a formal #2447 allocation.

## Scope remaining

Issue #2447 still requires endpoint-only vs temporal vs fail-closed comparison across at least three subgoals, independently scored per-subgoal effect and episode progress, held-out sequences/headings, and the stale/ambiguous/missing, delayed/dropped-frame, early/repeated false-signal, wrong-direction, focus-loss, timeout, restart, cleanup and recovery controls. No MAP01 clear, broad navigation, safety, timing-benefit, model, product or runtime-integration claim follows.

