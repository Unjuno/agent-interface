# Pre-freeze construction log

This local pre-freeze construction pass is not the formal T0 result.

- First independent agreement test: 4/5 tests passed; the full 39-row comparison failed on 9 reason-code rows. Candidate decisions were correct; candidate/auditor rejection-reason serialization differed. No formal run occurred.
- First correction pass: 4/5 still passed; 13 row reason-code mismatches remained because the auditor's reason precedence folded expiry/epoch into the basic receipt-validity predicate. No formal run occurred.
- Second correction pass: 5/5 tests passed, including exact 39-row equality, zero unauthorized effects under trusted single-use, weaker-baseline positive controls, UNKNOWN lost-response handling, release bypass, and 6/6 mutation rejection.
- Final host-only pre-freeze candidate CLI and separate raw-only auditor CLI each ran once; the auditor returned `PASS_METHOD_SCOPED`, 39 rows, 0 trusted-policy unauthorized effects, and 6/6 mutations detected. Their stdout is retained as `pre_freeze_raw.json`; it is excluded from the formal candidate denominator.

The frozen Docker candidate and Docker auditor remain uninvoked at this point. Any future container STOP or formal result is reported separately; pre-freeze construction does not erase or relabel the two failed intermediate checks above.
