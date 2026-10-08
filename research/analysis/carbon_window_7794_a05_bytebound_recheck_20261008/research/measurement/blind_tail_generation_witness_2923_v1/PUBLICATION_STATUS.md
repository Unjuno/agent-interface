# Recovery status — source freeze and excluded construction only

The original allocation `blind-tail-generation-witness-2923-20260923-01` remains
**formal 0/40**. This recovery preserves its exact source freeze and adds one
separately labeled excluded construction run. It does not claim or substitute
for the formal allocation.

- The source XZ capsule and all six frozen source-member SHA-256 values were
  verified during recovery.
- The 2026-09-30 construction exercised four IDs disjoint from the formal
  schedule; the frozen raw auditor reports four rows and `errors=[]`.
- That construction used an available ARM64 image with CPython 3.12.3 and
  Python-Xlib 0.33. The freeze requires Linux x86_64, CPython 3.13.5, and
  Python-Xlib 0.15. Therefore it is diagnostic construction evidence only;
  the frozen formal allocation was not started.
- The source runner does not retain Xvfb child exit codes in each row. The
  construction parent exited successfully, raw X11 requests produced all four
  rows, and Xvfb stderr (including non-fatal xkbcomp keymap warnings) is
  retained. Formal process-exit/provenance gates remain untested.
- No formal cases, controls, or corruption mutations were run during recovery.

Disposition: `HOLD_FORMAL_ENVIRONMENT_MISMATCH`. Issue #2923 remains open. Any
formal continuation must use the frozen environment and one-shot rules; do not
pool or relabel these four construction rows as formal evidence.
