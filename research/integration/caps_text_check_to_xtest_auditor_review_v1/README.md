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

The patch was applied only to a disposable copy of the two draft files. Four focused unittest cases passed: all three frozen-arm synthetic records remain accepted, a missing modifier release remains rejected, and balanced-bool-keycode plus press/release timestamp reversal mutations are rejected. The immutable A01 C01 raw record passed the proposed event predicates after only the declared v2 study-id and freeze-digest rebinding.

No public dispatch, GUI case, or formal allocation was run. This is a construction/auditor result only; it establishes no scientific result for the Caps Lock race.

## Integration conditions

Apply from repository root with `patch -p1 < auditor_event_contract.patch` only after the exact target files match the hashes above. Then rerun the complete v2 suite, add all new predicates to `FREEZE.json` mutation_controls and audit_event_contract, regenerate SOURCE_MANIFEST and freeze identities, test the instrumented construction path (including autorepeat behavior), and get independent review/readback before any A02 allocation. The per-key state machine is scoped to the fixed short XTEST fixture and is not claimed to handle general X11 autorepeat journals.
