# Issue #7678 — manipulation sensitivity T0 A02

Disposition: **PASS_METHOD_SCOPED**. Substantive result: **EXHAUSTIVE_NULL_FOR_DECLARED_SET_UTILITY**.

The fresh A02 OrbStack allocation executed its frozen candidate and independent auditor once each, both with exit code 0. The oracle reconstructed all 7,774 candidate rows exactly (169 truthful profiles × 2 reporters × 23 reports), including 7,178 report-dependent certificate changes. All four authority, protected-constraint, unknown-comparison and no-decision-right controls passed.

Under full information, safe-beneficial unilateral deviations: **0**. Under the declared partial-information partition (peer relation on a versus b only), safe-beneficial deviations: **0**. This exhaustive null is scoped to the explicitly declared possible-frontier set utility: a reporter values the best route in the presented frontier by their authored complete weak order. It is not a statement about how a human decision-maker would choose or how a real person would report preferences.

The result does not change the A01 disposition. A01 remains HOLD: its first frozen auditor failed before a valid audit and subsequent diagnostics were non-confirmatory. A02 is a separately identified, newly frozen allocation with exact predecessor and source provenance in PREDECESSOR_A01.md and FREEZE_A02.json.

## Reproduction and provenance

- Exact formal command and freeze-time source hashes: FREEZE_A02.json.
- Pinned image: python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f, linux/arm64; network disabled; 1 CPU; 1 GiB memory; 64 PIDs.
- Candidate raw matrix is published as lossless gzip at results/formal-01/candidate-output.json.gz; its compressed and decompressed SHA-256 values are recorded in RAW_OUTPUT_SHA256.txt. The auditor output is results/formal-01/audit-output.json.
- Invocation receipts and captured stdout/stderr: results/formal-01/RUN.json, candidate.stdout.txt, candidate.stderr.txt, auditor.stdout.txt, auditor.stderr.txt.
- Cgroup configuration observations and swap caveat: CONTAINER_LIMITS.txt. The cgroup diagnostic used a separate container with the same requested limits; the formal runner did not sample its own cgroup.
- SHA256SUMS covers all published package files except itself.

## Scope boundary

This is finite method evidence for two principals, three routes with identical requester-effect labels, all 13 complete weak orders, the specified 23-report domain and one explicit partial-information partition. It establishes no human strategic behavior or prevalence, fairness, consent, privacy, legal validity, coalition behavior, task effect, GUI safety, or production recommendation. Information was not hidden from anyone; no real workspace was involved.
