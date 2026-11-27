# Issue #1998 A05 first outcome

**Disposition: `HOLD_RUNNER_ERROR`; no scientific OCR result.** The frozen
candidate process was invoked once and exited 1 before launching Tesseract. The
formal wrapper therefore did not invoke the independent auditor. Retries: 0.
This allocation is consumed; neither candidate nor auditor may be rerun under
A05.

The retained stderr shows a harness defect at `candidate.py` line 34: the code
reads the local variable `tesseract` while hashing its executable before the
assignment at line 36. Candidate stdout is empty. No OCR output or crop
decision exists, and the six auditor mutation controls were not run. The frozen
frame, task oracle, 20 crops, Tesseract identity, and decision rule remain
unchanged; this outcome says nothing about whether a smaller crop preserves the
geometry markers.

## Custody

- Allocation: `LABEL-CONTROL-AMBIGUITY-1998-T0-A05-20261009`.
- Freeze commit: `ac5a6110a56267cc6634c9633af27ebeda51c728`.
- `FREEZE.json` SHA-256: `81fe3aba4922c2a22a94807ce4c144128451dccff1075810b3af0136ea9a07bb`.
- Candidate invocations: 1; candidate exit: 1; Tesseract child invocations: 0.
- Auditor invocations: 0; retries: 0; `audit.not_run` records the frozen conditional.
- The host sandbox network-denial smoke check passed before execution. Construction
  parser tests passed 3/3 under normal Python and 3/3 under `-O`.
- Formal command, exact retained raw hashes, and the absent start/end timestamp
  capture are recorded in `FORMAL_EXECUTION.md` and `RUN_RECORD.json`.

The scoped question is unresolved. This is a runner HOLD, not a scientific FAIL,
and does not alter the A04 payload-byte result or its excluded claims.
