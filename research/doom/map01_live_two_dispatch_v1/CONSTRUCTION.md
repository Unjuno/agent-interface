# Construction history

- `smoke-01`: harness incorrectly treated a single 0.5 s event-queue gap as the overall terminal timeout. No formal sample consumed. Repaired only the wait loop.
- `smoke-02`: core FRESH/STALE behavior passed, but the audit attempted to join `input_admission` by program id even though those events carry key/intent-token. This inverted the reported second-input counts. No formal sample consumed. Repaired the audit to count physical `Right` admissions directly and retain owner-expiry/terminal-score evidence.
- `smoke-03`: repaired construction boundary passed. It is not pooled into the formal three-pair result.
