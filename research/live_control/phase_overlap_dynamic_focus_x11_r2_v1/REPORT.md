# Dynamic phase footprint bound to current X11 focus — R2

Issue #1752.

## Construction

Construction one case/arm passed 4/4:
- static alternate-window write preserved A target X;
- resolved-bound alternate-window overlap preserved X and reduced both-effects wall time descriptively;
- resolved-bound focus-change serialized and preserved X;
- resolved-unbound focus-change redirected A to Y, giving the intended live selector discriminator.

## First formal outcome

The **first** formal invocation completed and was retained before any second invocation:
- static_alt 6/6 correct;
- resolved_alt 6/6 correct;
- bound_focus 6/6 correct;
- unbound_focus negative 6/6 redirected as expected;
- static median both-effects wall = 221.2273215 ms;
- resolved_alt median = 120.489612 ms;
- descriptive gain = 100.7377095 ms;
- first cleaned JSON SHA-256 = `beac98c8b58fab9ed654a06d75825669712ccd151260d4810e0b531d3ffd962d`.

However, python-xlib emitted Xauth warnings to stdout before the JSON body. The first wrapper attempted to parse the whole stdout as JSON, failed, and the operator then **incorrectly launched the same formal a second time** instead of parsing from the first `{` boundary.

The Issue froze formal exactly once / reruns0. Therefore the allocation is not eligible for scientific PASS even though the preserved first formal rows satisfy the substantive gates.

Disposition: `STOPPED_EXECUTION_PROTOCOL_UNAUTHORIZED_RERUN`; scientific disposition `NONE`.

The second invocation is excluded from scientific interpretation. No pooling or averaging occurs.

## Successor boundary

A fresh successor may change only output capture: send Xauth warnings away from the machine-readable result or parse the first retained result without rerunning. Scientific fixture, four arms, tails, counts, pixel/focus gates and thresholds must remain unchanged.
