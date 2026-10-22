# A01 run result

A01 is retained as `STOP_CANDIDATE_IMPORT`. Its candidate process started, but the intentionally incomplete `executor_v3` stub prevented the exact current-main V13→V12→V11 import before backend or input-owner construction. No fake XTest input was issued, the auditor did not start, and the candidate was not retried. A02 is a separately frozen successor using the actual `executor_v3` import.
