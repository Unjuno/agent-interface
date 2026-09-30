# Allocation 04 runner serializer repair: local construction test

## H / T / D / C / U

- **H:** Replacing the joined record's `event` field with `dict(row, event="joined_release")` avoids the duplicate-keyword `TypeError` while preserving every owner measurement field and leaving the source row unchanged.
- **T:** Apply the one-line serializer correction to an additive copy of the retained X11 runner. Exercise the exact helper with an existing event, a missing event, immutability, and JSON round-trip assertions.
- **D:** PASS for this serializer subgate if all focused tests pass and the corrected copied runner compiles. The formal X11 hypothesis is not evaluated by this construction test.
- **C:** This tests Python dictionary serialization only; it does not execute Xlib, Xvfb, Docker/OrbStack, input events, release timing, or the formal auditor.
- **U:** Passing does not establish that the full runner completes or emits complete/valid release evidence. Allocation 05 remains separately requested and unassigned.

## Result

The frozen Allocation 04 runner failed at `dict(event="joined_release", **row)` because each owner release row already contains `event`. A negative-control test reproduces that exact `TypeError`. The additive runner copy replaces that expression with a helper using `dict(row, event="joined_release")`. Five deterministic unit tests pass; the candidate runner compiles. No frozen artifact or Allocation 04 evidence was modified.

The first test invocation imported the full runner and stopped because host Python has no Xlib. The helper was moved into a standard-library-only module used by both runner and tests; the focused suite then passed without mocking Xlib or invoking a container.

This is a narrowly scoped construction PASS, not a formal X11 result. The next assigned one-shot allocation must freeze the corrected runner, exact image/platform, source hashes, and independent audit inputs before launch.
