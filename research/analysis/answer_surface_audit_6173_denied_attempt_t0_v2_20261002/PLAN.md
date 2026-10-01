# Issue #6173 T0 successor 02 — denied-attempt distinction

Allocation: `6173-T0-DENIED-ATTEMPT-DISTINCTION-02`.

## H / T / D / C / U

- **H:** In a finite synthetic scored-run fixture, a tool call to a scorer-only artifact that is denied is observably different from no tool attempt; a classifier that also ignores self-claims will retain that distinction without misclassifying legitimate task/document reads.
- **T:** Freeze main/source identity and a 13-case synthetic fixture. Candidate classifies only the candidate-visible access ledger. A separately authored auditor reconstructs dispositions from observer-side events, including denied oracle attempt, successful oracle bytes, oracle-derived artifact, allowed task evidence/docs, no attempt, missing monitor, unknown destination/recipient, mixed legitimate+oracle access, and untrusted self-claims. Run construction tests, candidate once, raw-only auditor once; no model, real answer, user data, GitHub/web retrieval, or network.
- **D:** `PASS_METHOD_SCOPED` iff all 13 classifications match the frozen expected classes; direct returned scorer-only bytes and known oracle-derived responses are flagged; a denied-only attempt is `ATTEMPT_BLOCKED` (not no-attempt); complete no-attempt is `NO_ORACLE_ACCESS_OBSERVED`; authorized task/docs remain authorized; missing monitor or unknown route/recipient is `UNKNOWN_ACCESS`; self-claims never override observed evidence; candidate and independent auditor both reject the planted false-clean and false-contamination assertions. Any candidate/audit mismatch is retained FAIL; missing/ambiguous monitoring is HOLD/UNKNOWN, not clean.
- **C:** Synthetic graph and event logs are complete by construction; real MCP/filesystem/web/network telemetry may be incomplete, artifacts may have unobserved derivatives, and fixed labels may not capture legitimate task-specific policy.
- **U:** This is finite method evidence only. It does not establish contamination in any real run, complete real-world monitoring, model behavior, or benchmark validity. Host CPU-only execution is used because other lanes' containers are active and the issue's T0 permits CPU-only graph/trace work; no active container is entered, stopped, or modified.

Source main at intake: `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`. Additive isolated path; preserve Issue #6173's T0 FAIL and audit-only adjudication unchanged.
