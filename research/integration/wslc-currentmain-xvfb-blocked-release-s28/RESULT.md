# S28 result — same-condition replicate

One preregistered fresh-session replicate at the same 3,930 ms pause as S27 passed its bounded test. WSLc observed pause: 3930.260725 ms. Public cancel response: 307.092677 ms. Supervisor release readback: 3987.763074 ms after admission; separate parent all-up readback: 4108.399033 ms. The cancellation transaction completed in 3995.201746 ms, 4.798254 ms before its 4,000 ms deadline. The delayed horizon remained all-up at 8502.317569 ms, with no late keypress.

The old task oracle and the fresh-session recovery task oracle both passed. The old public result correctly remained UNKNOWN/replay-denied/`task_success=null`. The independent 29-check audit is retained in `AUDIT.json`. S27 and S28 both passed at 3,930 ms with only 7.198 ms and 4.798 ms transaction margins; this two-sample repeatability check does not establish a hard timing guarantee or reliability. Synthetic private Xvfb only; no physical desktop, live application, MAP01, matched efficiency or product claim.

The WSLc session was terminated, while its unique 228,589,568-byte storage VHDX remains. Its SHA-256 is in [POST_CLEANUP.json](POST_CLEANUP.json). Host paths were redacted with original and sanitized hashes in [REDACTIONS.json](REDACTIONS.json).
