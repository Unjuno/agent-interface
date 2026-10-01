# Issue #6102 T0 — finite nested-return semantics

## Scope and H/T/D/C/U

This is a finite exact analytical experiment over a frozen two-generation event alphabet, lengths 0–6, and maximum modeled nesting depth 3. No GUI, model, application, input, or live authority is involved.

- **H:** For balanced nested modal traces, a flat depth-only flag can accept wrong-parent returns; a parent-identity stack and a correctly depth-matched finite-state encoding agree on all traces in their declared finite domain.
- **T:** Enumerate every word over `open(A), open(B), close(A), close(B)` for lengths 0 through 6. Independently score exact LIFO parent matching, compare it with a flat depth-only acceptance gate and with a depth-3 FSM versus a literal bounded stack. Over-depth traces yield UNKNOWN, not rejection-as-success.
- **D:** `PASS_METHOD_SCOPED` only if independent counts and per-trace decisions agree; stack/FSM have zero disagreement where the FSM is defined; flat depth-only has at least one wrong-parent acceptance among balanced words. Otherwise FAIL for a decision mismatch, or HOLD if enumeration is incomplete. No general-depth or live GUI claim.
- **C:** A fresh source-bound current-parent observation or direct application API may avoid maintaining a stack; shallow bounded applications may use an explicitly expanded FSM with identical correctness.
- **U:** Finite alphabet, bounded length/depth, perfect event capture, and exact generation identity are assumptions. This does not test missing events, ID reuse, concurrent windows, non-LIFO application semantics, or task effects.

## Frozen allocation

Allocation: `MODAL-RETURN-6102-T0-20261002-01`.
Formal execution is permitted only after source hashes are recorded in `FREEZE.json`. The initial construction defect (accepting nonempty terminal stacks) is retained as `CONSTRUCTION_FAILURE.md`; the corrected implementation below is a distinct, pre-formal source freeze, not a retry of a formal allocation.

## Executed command

`python experiment.py` and `python audit.py` from this directory. Exact finite enumeration is platform-independent CPU work and does not require container isolation. Docker Desktop's configured Linux Engine endpoint was probed, but `docker ps` did not return within the 10-second command window; no container execution is claimed.
