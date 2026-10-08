# A15 protocol

## Question
Do explicit typed eligibility examples reduce false, premature, or malformed conflict claims while preserving the schedule comparison’s fixed episode stream and intermediate memories?

## Allocation
- ID: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A15-TYPED-CONFLICT-ELIGIBILITY-20261008`.
- Fresh seeds 5501, 5502, 5503; four arms; six checkpoints; five held-out queries.
- 360 query calls plus 30 consolidation calls = 390 planned calls.
- Model: `qwen3:8b`, frozen digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Dedicated private Ollama service on loopback port 11435 and store `/tmp/unjuno-8406-t1-a15-ollama-store`.

## Intervention and controls
Relative to A14, the only intervention is a rewrite of the prompt’s conflict specification. It makes eligibility depend first on exact claim kind, explicitly excludes every non-fact kind, gives four symbolic cases, and uses a consistent string value in the generic conflict shape: different verified patterns do not conflict; a single fact does not conflict; equal same-scope fact values do not conflict; differing same-scope fact values do conflict. It retains cross-boundary rescanning. No fixture literals are added to the prompt. JSON Schema, model, decoding, fixture, schedule, query, and auditor controls are held fixed.

## Execution and gates
1. Freeze this package and post preregistration to #8406 before model generation.
2. Verify private tag digest and every manifest blob; preserve preflight JSON/checksum.
3. Run the candidate exactly once. Do not retry, replace seeds, or pool allocations.
4. If and only if all 390 calls complete and all rows are present, run the independent auditor exactly once.
5. Save raw and audit artifacts and checksums, then stop the private service.

Identity mismatch before generation is STOP with zero calls. Any interrupted/error call or incomplete row count is STOP/INCOMPLETE without retries. Any auditor error or non-PASS_METHOD result is FAIL_METHOD; all endpoint contrasts remain descriptive and no schedule conclusion is allowed. A clean PASS_METHOD is still scoped to this synthetic ledger, model, prompt, and seeds; it does not establish GUI effectiveness or a production policy.
