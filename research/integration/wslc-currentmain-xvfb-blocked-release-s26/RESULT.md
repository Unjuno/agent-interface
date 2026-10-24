# S26 WSLc current-main private-Xvfb 3940 ms boundary replicate

The independently preregistered 3,940 ms replicate crossed the exact 4,000 ms transaction deadline. The cancellation transaction completed 4,003.517 ms after admission, 3.517 ms late. The public result correctly remained `UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`; the release attempt was reported `UNKNOWN / transaction_deadline`. No independent release receipt or task-effect oracle was emitted. The standard-caller test failed its disconnect assertion as expected for this registered boundary branch.

Audit: 22/22. Exact Xvfb process termination and container/image/session cleanup completed. The cleanup record retains the expected nonzero test exit as a failure field; it does not indicate a failure to remove resources. No retry was made.

S26 independently replicates S25's 3,940 ms pause. S25's release receipt was 7.614 ms before deadline but its independent all-keys-up check missed the 5,000 ms bound by 2.641 ms; S26 shows the transaction itself crossing the deadline by 3.517 ms. This confirms that 3,940 ms is beyond a stable guaranteed boundary in these samples. Private synthetic Xvfb only; no physical GUI, real application, MAP01, efficiency or general reliability claim.
