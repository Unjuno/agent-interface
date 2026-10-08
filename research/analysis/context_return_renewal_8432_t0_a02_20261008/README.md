# Issue #8432 — context-return renewal T0 A02

This new allocation corrects the A01 episode-denominator inconsistency without
modifying A01. A01's retained method-gate failure remains authoritative for
that allocation; its separate post-publication raw-byte identity discrepancy
also remains unresolved. A02 generates a fresh deterministic fixture and does
not use A01's raw bytes as input.

A02 has three context paths (`return_A`, `continue_B`, `novel_C`), two cue
identity strata, and three history conditions (`chronological`,
`context_tagged`, `none`): 18 episodes total, of which 12 have matched
non-empty histories and six are explicit no-history controls. Each contains
the ordered A-acquisition/B-correction history (when assigned), a four-trial
B-baseline test, then a four-trial return-A/continued-B/novel-C test. The split
is derived from the Cartesian product and independently reconstructed; no
stdout episode count is hard-coded.

The assay tests only deterministic materialization, denominator/support
integrity, a synthetic scorer control, and mutation rejection. It makes no
model-behavior, animal-learning transfer, GUI, safety, human, or product claim.
