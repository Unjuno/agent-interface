# Issue #7462 T0 — effect-safe finite equality saturation

This no-model T0 compares a frozen source program, a strict-improvement
fixed-order greedy rewriter, and bounded finite equality saturation with
minimum-cost extraction. It uses three small typed programs and an independent
exhaustive state/effect interpreter. It tests a source-level transformation
method only; it is not a production e-graph, GUI optimizer, or runtime result.

The only semantic rewrites are ASCII `TRIM`/`LOWER` commutation and idempotence
inside an immutable pure-value expression, plus removal of adjacent identical
side-effect-free passive checks. No rewrite crosses a freshness, world-change,
edit, save, release, or terminal boundary. The held-out program combines a
pure commutation bridge with a freshness barrier and ordered edit/save plus
success/UNKNOWN exits. Three planted invalid candidates remove refresh, swap
edit/save, or drop release; the independent checker must reject each.

The recent macOS OrbStack read-only preflight in #7487 stopped on
`STOP_ORBSTACK_DAEMON_BLOB_READ`; no image acquisition or daemon retry is
authorized. This exact finite standard-library method test is therefore
host-only and is not isolation/container evidence. No participant, model, GUI,
formal allocation, or external effect is involved. See `FREEZE.json`,
`PROTOCOL.md`, and the formal run record for the exact boundary and hashes.
