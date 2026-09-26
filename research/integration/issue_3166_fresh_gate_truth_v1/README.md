# Issue #3166 — fresh commit-gate truth first rung

Container-first, additive first rung for the still-open live acceptance gap in Issue #3166. This
tests a stable prepared dependency while the commit gate changes truth/freshness/lineage, using a
real private GTK/X11 effect fixture. It does not complete the issue's full five-policy/malformed,
duplicate-commit, absent/contradictory-postcondition acceptance matrix.

See `PREREG.md` for H/T/D/C/U and frozen gates; after execution, inspect the immutable result and
`COLLISION`/STOP notes before treating any status as evidence. No source-runtime code is changed.
