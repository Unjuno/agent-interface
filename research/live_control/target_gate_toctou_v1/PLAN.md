# Frozen plan — Issue #965

Publication BASE: `98c6bece2a46e04c3a872dbd45133afe18cb80a6`.

H: a target patch that is fresh and correct at check time cannot by itself authorize a later semantic click after a same-surface target/decoy mutation.

T: private Xvfb/Tk, exact 11x11/radius5/max-error<=8 pixel gate, one XTEST click at the frozen A coordinate. Six matched pairs / twelve fresh sessions in counterbalanced order. `swap` changes only post-gate app state and is acknowledged before the click. No observation occurs between the gate and click in either arm. One formal block invocation; reruns/replacements/tuning 0.

D: PASS_TARGET_GATE_TOCTOU_EXPOSED_SCOPED only if all pre-action gates pass; stable 6/6 clicks task-target; swap 6/6 mutations occur strictly after gate and before click and clicks decoy; swap final A patch differs from gated A patch by >8; exactly one click/case; terminal Button1 up; source/result/audit integrity passes.

C: synthetic adversarial mutation; coarse focus/surface/geometry guards may catch other changes, but this same-surface semantic mutation need not alter them.

U: Linux/X11/Tk only; no natural mutation-rate, model, token, productivity, cross-backend or production-security claim.
