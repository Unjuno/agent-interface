# Post-result adjudication — 8661-T0-A01-20261009

Formal disposition is **`HOLD_CANDIDATE_SELF_CERTIFIES_TERMINAL`**. The frozen candidate and auditor each ran once, and the original auditor output `PASS_METHOD_SCOPED` is preserved unchanged. A post-result code-path review found that `candidate.py` computes `terminal_verified` from its own simulated terminal error and immediately supplies that boolean to its update decision. The candidate therefore self-certifies the completed episode; no separately produced independent terminal/effect receipt enters the training update path.

The auditor independently recomputes the same rows after execution, which supports the reported numerical contrast but cannot make the candidate's update-time evidence independent. The boundary probe for an unverified terminal proves refusal when given a false flag, but does not establish that training updates consume an independent verifier result. The Issue's explicit condition—update only after an independently valid completed episode—is therefore unverified, so the formal D gate remains HOLD despite the favorable finite metrics.

This adjudication changes no source, fixture, candidate output, or original audit, and no candidate rerun occurred. A later successor would need a separate verifier-produced receipt as a frozen candidate input and a distinct allocation; this record does not launch it.
