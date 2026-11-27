# Post-result adjudication — EIR-8620-T0-A01-20261009

Formal disposition is **`HOLD_FORMAL_FREEZE_INCOMPLETE`**. The candidate and both auditors' original outputs remain byte-for-byte preserved. Auditor v1 returned `FAIL`; diagnostic auditor v2 rechecked only the retained candidate raw and confirmed the finite fixture predicates, but it cannot repair a pre-execution freeze omission.

`FREEZE.json` specified “macOS host CPython 3.x” and deferred the exact version to a raw record. The actual CPython version (3.14.5) was queried after the candidate invocation, and the raw candidate JSON does not contain it. Thus the runtime was not fully frozen before execution, contrary to the requested formal protocol. The v2 diagnostic remains useful evidence about the output, but the experiment is not promoted as a formal PASS. No candidate rerun is authorized by this adjudication.

The separate OrbStack preflight STOP is also preserved. This formal HOLD is independent of that infrastructure STOP; the no-container host fallback was permitted by Issue #8620 but its exact runtime was not preregistered.
