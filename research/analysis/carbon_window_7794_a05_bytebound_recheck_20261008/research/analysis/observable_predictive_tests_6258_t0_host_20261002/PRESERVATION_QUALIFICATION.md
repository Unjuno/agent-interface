# Preservation qualification (2026-10-02)

This package is integrated as an explicitly qualified historical, host-only finite research record. Integration does not independently endorse the original `PASS_METHOD_SCOPED` label as a new scientific or runtime result. Existing source, report, freeze, run record, manifests and raw outputs remain unchanged; their historical labels are preserved.

## Published-byte discrepancy

At reviewed PR head `2e2cc06b364575945d989b45420f5f135aec93e8`, the committed raw JSON bytes differ from the original report and SHA256SUMS:
- `candidate.raw.json`: committed 7,685 bytes, SHA-256 `638244d58d2836bc6e404acc560356c8e4b99185be13cf3ca49b08b2ead3b562`; recorded 8,043 bytes, SHA-256 `aa8c1df2966bab84d797030723a2a401fad5da2e71140a4958eae2f7a6cd613e`
- `audit.raw.json`: committed 190 bytes, SHA-256 `59420c3c830998a2353ef37dec093fb70fc38262e156304d0fd3837f82b0a88f`; recorded 198 bytes, SHA-256 `daa18a101be85eae7f251ceb2be6d16b899ac6230a895169135be63c6d844879`

A diagnostic LF-to-CRLF transformation of the committed bytes exactly reproduces both recorded sizes and hashes. This identifies a newline-representation discrepancy; it is not a newly recovered contemporaneous artifact. No transformed replacement was committed and no manifest was rewritten. The four candidate/auditor/test/PLAN source hashes match FREEZE.json.

## Interpretation and preservation

The retained auditor output reports nine authored cases and 66 transition outputs with zero mismatches. That historical report is not substituted for integration review or a broader validity claim. The original candidate and auditor were not rerun during integration, and no new allocation was consumed. Prior or parallel Issue #6258 records remain distinct and unchanged.

Issue #6258 remains open. No PSR learnability, live test-vocabulary completeness, long-horizon behavior, GUI/model/user effect, route conformance, production safety or runtime promotion follows from this preservation merge.
