# R44 — paired bounded release and fresh-generation task oracle

Status: prepared; no R44 fixture or input has started.

R44 tests the full same-attempt chain: bounded cancellation release, finite recovery witnesses, then one independently scored task on a distinct fixture generation. The phase-2 harness includes R43's corrected `user32` handle scope. The runner starts phase 2 only after every frozen strict phase-1 gate passes.

Both fixtures require a unique CUA activation receipt and independently confirmed foreground HWND before public observation or dispatch. Any mismatch, timeout, harness failure or incomplete receipt is FAIL_OR_UNKNOWN; never retry or replay. Native Windows evidence does not establish WSLc eligibility, MAP01, broad reliability, matched efficiency or real-application transfer.
