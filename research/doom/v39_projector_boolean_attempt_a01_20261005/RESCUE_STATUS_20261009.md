# Evidence rescue status — 2026-10-09

This folder preserves the original A01 report from closed-unmerged PR #8132, head `c405b129e83c613e815160f841070ed68267be1d`. `REPORT.md` is copied byte-for-byte from that head; no candidate, test, or probe was rerun for this rescue.

The report is a historical falsification on frozen main commit `f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c`. It must not be read as evidence that current main rejects boolean attempt ordinals. At current main `6afcfccc0b709b1b7ab9dc50acc03afd60a7e3d1`, the projector compares `attempt.get("attempt")` with its ordinal using equality without an exact-type guard, so Python's `True == 1` remains relevant.

The broader repair proposal is open Draft PR #8139. It carries the exact-integer predicate and regression property alongside wider identity-matching changes, but has zero submitted reviews and has not merged. This archive integrates neither that candidate nor the #8132 code patch; it preserves only the prior finding and its recorded limits. Revalidate against current main before making any present-tense behavior claim.
