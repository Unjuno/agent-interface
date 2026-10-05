# Issue #7678 T0 A01 — formal failure retained

**Disposition: HOLD; this is not a confirmatory PASS.** The single frozen candidate completed, but the first formal auditor exited 1 because freeze metadata was missing. Audit code and freeze metadata were changed after execution before a later diagnostic auditor printed PASS. The diagnostic is non-confirmatory; the candidate and allocation were not rerun. The original missing auditor stdout/stderr cannot be recovered, and no REPORT.md was issued.

Preserve the exact candidate output, failure account, amended freeze, audit attempts, and append-only review corrections in [the formal record](results/formal-01/AMENDMENT.md), [RUN.json](results/formal-01/RUN.json), and the package README. Review-correction-04 rechecked all 7,774 deviation rows and metadata but explicitly leaves the formal allocation at HOLD. This finite synthetic study makes no claim about real human behavior or withholding information.
