# Kernel receipt-time research intake

Decision: **HOLD_RUNTIME_ADOPTION**. This preserves the original #5215 outcome; it does not relabel the scientific record as a runtime failure or rerun its allocation.

The six original evidence hashes match their published manifest. Both published Git blob IDs match the frozen source. The first local intake stopped because the published SHA-256 values differ from Git blob bytes; an explicit follow-up established they match CRLF checkout bytes. This explains the representation distinction, rather than silently normalizing a failed identity check.

The retained original auditor reproduces PASS_TEMPORAL_RECEIPT_GAP_SCOPED on the complete stored record. Three copied-record controls remove all four temporal-negative fields, replace them with null, or replace them with strings. Each returns NO_GAP_OBSERVED with no errors. Missing or mistyped evidence must not support a no-gap conclusion in a successor auditor.

There are also prospective-contract inconsistencies: PLAN case 7 says to reject effect time 700, while the auditor requires acceptance. The plan's baseline mentions effect time 900, which the probe does not exercise. Resolve these explicitly in a successor; preserve this allocation and its original reported findings.

Current public MCP execution uses core_v1 and native backends, not RequestLifecycle. A kernel ingestion rule is not evidence of an enforced public input deadline. Before runtime integration, define the clock domain, action cutoff versus release/capture completion, delayed receipt delivery, and how to retain already-occurred effects if temporal evidence is rejected. A late receipt must not imply no input occurred.

Run `python3 runtime/results/kernel-time-intake-01/check.py` from the repository root. It checks retained identities, reads frozen Git sources, reproduces the stored audit and writes result.json from copied-data controls. It does not execute the scientific probe, create a GUI session, use a model or send input. Original files are copied verbatim under source/ for review. This is integration intake, not a speed, reliability or token result.
