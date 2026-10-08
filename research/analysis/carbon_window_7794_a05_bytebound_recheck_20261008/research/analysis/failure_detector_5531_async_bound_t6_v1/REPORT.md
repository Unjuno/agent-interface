# #5531 T6-E1 result — bounded asynchronous delay indistinguishability

The corrected independent audit passes on the exact preserved T6 candidate
trace: `PASS_ASYNC_DELAY_BOUNDARY_SCOPED_AUDIT_V2`, 18 trials, 114 JSONL rows,
6 identical-prefix groups, 0 effectful actions. At deadline, timeout-as-failure
permanently failed the healthy-slow subject in all 3 deadlines; typed suspicion
blocked routing without permanent revocation in all 3. Independent crash proof
then caused terminal failure, and stale responses did not reactivate it.

Raw SHA-256:
`876868a980214b6659fc928969e3fb2e60449879105fd697c4c3c2c16a8ac0f6`.
The first v1 audit omitted checks for authenticated proof fields; its PASS is
preserved but not accepted. A separate v2 auditor verified authentication,
generation, domain, exact event schedule and raw identity. Candidate was not
rerun. See `results/t6-e1-01/` for the preflight manifest STOP,
`results/t6-e1-02/` for immutable candidate/raw/v1 output, and
`results/t6-e1-03-audit-correction/` for the corrective audit.

Host-only finite logical-time evidence. Docker was unavailable and no shared
allocation was requested or consumed. This is not a general asynchronous
failure-detector theorem or runtime/production safety result; Issue #5531
remains open.
