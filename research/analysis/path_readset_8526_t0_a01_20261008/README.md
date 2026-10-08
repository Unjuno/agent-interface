# Path-conditioned read-set T0 A01 — Issue #8526

This package tests whether a complete typed path certificate can preserve a semantically valid late result across changes confined to an unexecuted branch without admitting stale, hidden-read, unknown, ABA, generation-changed, or late results.

The frozen protocol, decision gates, and scope limits are in `PROTOCOL.md`. `candidate.py` emits a finite 13-case × 3-policy matrix; `audit.py` is independent and does not import the candidate. `FREEZE.json` records source hashes and environment before formal execution. Formal evidence is retained under `results/`.

This is synthetic method evidence only. It does not establish complete dependencies for any real agent/model/GUI computation and grants no authority or action capability.
