# Formal allocation A01 — HOLD_AUDIT_EXECUTION_FAILURE

The candidate CLI ran once and emitted eight rows (exit 0; raw SHA-256 `4e4f95a92add0cc8f19ae7f10725e21905ab81116f7db17847e0abd26fc277d0`). The separately invoked auditor ran once and exited 1 with `RecursionError` because corruption checks recursively called the full check. No audit output was written; retries=0. Do not call this allocation a PASS.

Downstream A03 Issue #6843 performed a separate, independently preregistered audit-only reconciliation of the preserved raw output and passed its exact row/truth/mutation gates. That supplemental result does not rewrite this A01 execution failure. Scope is authored 2-D synthetic tracks and stipulated layer identity only; no real-scene, GUI/game, contact, task-benefit, safety, or product claim.
