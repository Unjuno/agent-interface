# MAP01 matched recovery entry gate oracle-shape repair (#2346)

Successor to #2339. The original evidence is preserved. The current-main defect was that `decide()` emitted `authority` while `oracle()` omitted it, so exact comparison could not execute.

## H/T/D/C/U

- H: repair only the oracle shape by adding `authority: False`; do not change thresholds or readiness semantics.
- T: native Python and `python:3.12-slim` must complete the exact 32-vector comparison and emit the scoped PASS line.
- D: `PASS_MATCHED_RECOVERY_ENTRY_GATE_HOLD_SCOPED vectors=32 authorize=1 current=HOLD controls=5/5`.
- C: readiness-only; no MAP01 allocation, model, GUI/X11, input, network authority, or production claim.
- U: live MAP01 readiness and task recovery remain unverified.

## Evidence

Native and container runs both emitted the exact expected line. The change is limited to oracle-shape parity; `authority=False` remains non-authorizing.
