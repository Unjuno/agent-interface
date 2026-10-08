# Successor 02 — independent-oracle error-set correction

Allocation 01 remains unchanged and retains `FAIL_RAW_AUDIT`. Its candidate emitted two valid simultaneous findings in each of the invented-permission and mismatched-span cases: the derived addition/reference was invalid, and the original source clause was also uncovered. Allocation 01's auditor incorrectly required a single error class. This successor changes only those two independently adjudicated expected error sets; it does not alter candidate code, cases, thresholds, or raw result. The original candidate is not rerun. This is a corrected independent re-audit of the same frozen candidate output, not a new candidate experiment and not a claim about language-model extraction.

## Frozen discriminator

All eight candidate rows must match the independently specified outcome and complete error set. The corrected expected sets are:

- `invented_permission`: `SOURCE_CLAUSE_OMITTED` + `UNSUPPORTED_DERIVATION`.
- `source_span_mismatch`: `SOURCE_CLAUSE_OMITTED` + `SOURCE_SPAN_MISMATCH`.

All other expected outcomes/error sets are identical to allocation 01. The exact candidate raw file is SHA-256-bound below. The audit script is frozen before its single invocation. A mismatch remains a failure; no retries or edits after the invocation.

## Scope

Passing this audit repairs the auditor taxonomy mismatch only. It does not turn allocation 01's originally preregistered `FAIL_RAW_AUDIT` into a pass, establish model behavior, validate natural-language atomization, or satisfy a Docker/live allocation.
