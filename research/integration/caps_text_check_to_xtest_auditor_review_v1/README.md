# A02 raw-event auditor patch proposal

This additive review artifact supplies a reproducible patch proposal for the unpublished A02 protocol draft in Issue #8328. It does not alter the A01 record, production code, or the source branch.

## Target snapshot

- Local draft commit reviewed: `987589c63f5a98d2543f3d23b0d5838fe172764c` (not published on GitHub at review time)
- Draft `FREEZE.json` SHA-256: `0bab3d9a741e7dbe0ce09c2d3d4e9278da81f5386ab0294a119b971c8977a9bd`
- Pre-patch `audit_formal.py` SHA-256: `a466e81c257468fdac745192e5af1e0fd71beeeb7374fcfa26c433e249db568b`
- Pre-patch `test_audit_formal.py` SHA-256: `edb66e120faa009d813c73f7821539ae58ffafcebf441f4a60c703a8a9395879`
- Branch creation base: main `b8bec9a05da31ae722968bd49a30879b07df1a2e` (ancestor of current main)
- Current main/PR base at PR creation: `a273aa14c0d188cd385fbcec09d4585b2b61fea6`

## Review finding and proposed correction

The existing `isinstance(keycode, int)` check accepts JSON booleans in Python. The event audit also checks payload-character order and keycode Counter balance but not timestamp ordering or per-key event chronology. The attached patch switches to exact-int keycodes, validates nondecreasing integer timestamps for KeyPress/KeyRelease events, and checks balanced per-key state in event order.

## Construction validation

The patch was applied only to a fresh disposable copy of the two draft files. The first full-suite attempt stopped before audit execution because the copy lacked XVFB_EXPECTED_STDERR.txt; after copying that declared fixture, the complete v2 auditor suite passed 8/8. The suite covers all three frozen-arm synthetic records, a missing modifier release, both new keycode/timestamp mutations, material corruptions, frozen schedule/mutations, the draft allocation gate, and the immutable A01 C01 raw record under only the declared v2 study-id and freeze-digest rebinding. The initial missing-fixture stop is a preserved setup failure, not an auditor or scientific result.

No public dispatch, GUI case, or formal allocation was run. This is a construction/auditor result only; it establishes no scientific result for the Caps Lock race.

## Integration conditions

Apply from repository root with `patch -p1 < auditor_event_contract.patch` only after the exact target files match the hashes above. Then rerun the complete v2 suite, add all new predicates to `FREEZE.json` mutation_controls and audit_event_contract, regenerate SOURCE_MANIFEST and freeze identities, test the instrumented construction path (including autorepeat behavior), and get independent review/readback before any A02 allocation. The per-key state machine is scoped to the fixed short XTEST fixture and is not claimed to handle general X11 autorepeat journals.


## Container execution gate

A later read-only OrbStack check found Docker Engine 29.4.0 Linux/ARM64 responds, but inspecting the locally named `python:3.12-slim` image stops on missing/unreadable containerd blob `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`operation not supported`). No container test was started, and no pull, prune, reset, or daemon repair was attempted. The 8/8 suite above was host-only construction validation performed before this fresh container gate check; it is preserved but does not satisfy the repository's preferred isolated-container execution rung. Do not rerun it on the host as a substitute. Recheck only after the container content store becomes usable or an explicitly applicable frozen protocol authorizes a different environment.