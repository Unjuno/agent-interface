# A02 — owner-reference harness STOP

**Disposition: STOP during candidate setup.** The candidate confirmed the Xvfb alias precondition (`a` and `A` map to code 38), started the actual V4/V3/V12 owner, then stopped while the harness attempted to inspect `owner._inner._inner`. The actual V4 wrapper inherits the V3 initializer, which stores V12 directly as `owner._inner`. No key-down or alias batch occurred. The candidate's `finally` called `owner.close()`; Xvfb exited 0.

The frozen raw-only auditor retained `STOP` with 3/11 structural checks passing (alias mapping, no pre-close explicit key-up record, and zero Xvfb exit). Raw SHA-256: `84a168483e6843e32075fb2eff0d5802e2970df23339cdd820427e8b8cbd62a6`. Audit SHA-256: `44a0dabd83638a20c2343c5a3a7a81fe63f8d1cbbf72f65dfd4a0eb6c286e662`.

This is a harness construction STOP, not a release failure. A03 changes only the candidate's owner-reference lookup and uses its own output directory.
