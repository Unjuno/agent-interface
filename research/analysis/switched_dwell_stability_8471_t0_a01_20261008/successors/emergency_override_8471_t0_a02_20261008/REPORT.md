# A02 result — emergency override during dwell

**Disposition: `PASS_METHOD_SCOPED` for the abstract override protocol only.**

The frozen candidate and independent auditor each ran once using CPython 3.14.5 on Darwin arm64. The candidate emitted all 20 combinations of current mode A/B and elapsed dwell ticks 0 through 9, with an emergency request for the alternate mode. The independent audit reconstructed 20/20 cells. Every cell selected the requested alternate mode on the same tick with zero delay and confirmed that normal dwell would otherwise retain the current mode. The three mutations (normal guard suppression, hold-current, one-tick delay) were all rejected.

Raw candidate SHA-256: `178752deba652ff673af670516b0a1c67b639bd914353441d9527bb16a8cb4fb`.

This is an abstract policy truth table, not execution of a controller, safety monitor, actuator, or real emergency path. A01 remains unchanged. Combined A01/A02 covers the finite method gates declared in these allocations; it does not close Issue #8471's future read-only trace eligibility or establish any production-safety result.
