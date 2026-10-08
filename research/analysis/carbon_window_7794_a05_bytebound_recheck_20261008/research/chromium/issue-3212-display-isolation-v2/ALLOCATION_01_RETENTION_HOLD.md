# #3419 allocation 1 — gate observations with retention HOLD

Decision: HOLD_RAW_MANIFEST_MISSING

## H/T/D/C/U

- H: A p1→p2 generation transition with a p2/decoy pair can reject the old p1 target, prevent decoy input from mutating p2, and admit exact p2 input/effect.
- T: Fresh Debian bookworm-slim Chromium/Xvfb/Openbox allocation. p1 on :280/CDP 9391 was terminated; p2 and decoy ran on :281/CDP 9392/9393. Old p1 target was attempted, decoy then p2 received x, and titles were read independently.
- D: The terminal gate line and observed receipts are retained here. This allocation did not persist raw JSONL plus a SHA-256 manifest inside the container, so the scientific acceptance gate is not PASS.
- C: Formal PASS requires raw JSONL, source/runtime identity, independent audit and manifest in addition to the gate values.
- U: No broad GUI reliability or product claim; do not relabel this HOLD as a scientific failure.

## Observed gate output

OBSTAC_3419_FORMAL_ALLOCATION PASS old_target=rejected decoy_after=os-input-decoy p2_after_decoy=p2-ready p2_after_own=os-input-p2 p1_xid=4194307 p2_xid=6291459 decoy_xid=4194307

The old p1 target was rejected. Input to the decoy changed only the decoy; p2 stayed p2-ready. Input to p2 then produced os-input-p2. These are gate observations only because raw retention was incomplete.

## Recovery

Do not rerun or mutate this allocation. A fresh allocation must create raw JSONL, manifest and independent audit before the first gate event, then repeat the same frozen topology and predicates.
