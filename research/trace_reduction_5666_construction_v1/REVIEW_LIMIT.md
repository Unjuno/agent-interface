# Source-review limitation: one-minimality is vacuous in v2

Read-only review of the published `check.py` (PR #5669; 2026-10-01) found that the reported `one_minimal_under_declared_grammar` assertion is automatically true after removing `noise`: the five remaining nodes are exactly `REQUIRED`; every one-node deletion therefore fails `legal()` regardless of `simulate()`'s fingerprint. This is not an effective minimality or search-algorithm test.

The other synthetic checks retain their narrow meaning: the authored `noise` deletion preserves the fingerprint, deleting grant/release changes the typed failure despite equal exit code, and an act-before-grant reordering is rejected by the grammar. `audit_blackbox.py` calls candidate functions and is not a raw-only audit. No real retained GUI failure is replayed.

Disposition remains **CONSTRUCTION_CHECK_ONLY / T0 HOLD_NO_REPLAYABLE_FAILURE**. No source or previous output is rewritten by this note. A stronger construction needs a legal single-deletion competitor and an actual reducer; empirical qualification needs replayable real failure and independent effect/release oracle. See Issue #5666 and PR #5669 source-review comments.
