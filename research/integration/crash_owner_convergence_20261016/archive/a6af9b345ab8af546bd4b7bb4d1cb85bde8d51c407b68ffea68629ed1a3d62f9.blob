# A09 controlled-Xvfb-exit successor

A08 met every input-owner process-recovery gate, but its frozen final control assertion required Xvfb return code -15 while the supervisor's terminate request produced clean code 0. A09 carries the successful corrected `a` probe, durable event log, LF runner, and recovery gates forward. It records whether the supervisor sent Xvfb termination and accepts only a clean return code 0 or signal-derived -15 after that request. This is an explicit new decision rule under a new allocation, not an A08 relabel.

One candidate invocation; no retries. PASS_METHOD_SCOPED still requires all independent down/up, session SIGKILL, receipt, clean owner exit, and controlled Xvfb termination evidence. No broader product claim.