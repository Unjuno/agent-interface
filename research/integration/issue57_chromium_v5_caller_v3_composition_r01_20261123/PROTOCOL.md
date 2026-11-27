# Chromium V5 handles through adaptive caller v3 R01

## Question

Can the exact V5 point-mint method and real session-scoped `TargetHandleStore`
feed the existing adaptive caller v3 → compiled GUI v2 chain, with actual
per-action handle resolution as admission, and does that chain refuse the next
action when a target generation changes after a completed/released prefix?

## Frozen cases

1. **Positive:** point-mint separate textured `field` and `submit` aliases from
   the exact V5 method; v3 reuses them, final revalidation constructs a
   compiled two-step form method, both references resolve and are admitted,
   both fake actions complete with verified release, core effect checks pass,
   and the separate outer scorer reports task success.
2. **Changed generation after first action:** switch only window generation
   after the first action returns verified release. The subsequent compiled
   observation still matches the form predicates, but real handle resolution
   must return `SCOPE_MISMATCH`; submit must not execute. Caller output must
   retain `EXECUTION_INCOMPLETE` / `confirmed_partial`, one completed
   transition, and no outer task-success verdict.

The V5 point-mint method, real target-handle store, caller v3, compiled runtime,
and form compiler are invoked locally with synthetic pixels and fake I/O. No
browser, X server, operating-system input, model/provider, or user desktop is
used. These tests validate the composition seam only; they do not measure
economics. One normal and one `-O` process execute the frozen 25-test suite.
Any failure is retained and not retried under this run ID.
