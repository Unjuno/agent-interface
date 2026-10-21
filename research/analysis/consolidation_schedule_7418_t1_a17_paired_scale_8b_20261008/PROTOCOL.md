# A17 protocol

## Question
With seed values, prompt, fixture, schedule, decoding, and auditor held fixed, does Qwen3 8B reproduce A16's transition fidelity and schedule-sensitivity outcome observed with Qwen3 14B?

## Allocation
- ID: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A17-PAIRED-SCALE-8B-20261008`.
- Same seeds as A16: 5601, 5602, 5603; four arms; six checkpoints; five queries.
- 360 query calls plus 30 consolidation calls = 390.
- Model: `qwen3:8b`, Q4_K_M; frozen digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Dedicated store `/tmp/unjuno-8406-t1-a17-ollama-store`, loopback port 11435.

## Single intervention and controls
Relative to A16, only model scale changes from Qwen3 14B to Qwen3 8B. The prompt, schema, fixture, queries, schedule arms, decoder, auditor, and numeric seed values are held fixed; prompt/query hashes are checked in the construction suite. The same numeric seeds allow direct per-seed comparison, although random streams are not assumed to be coupled across different model sizes. A17 results are not pooled into A16.

## Execution and interpretation
1. Freeze and preregister before generation; run read-only private tag/blob preflight.
2. Invoke the candidate once. No retries, replacements, or pooling.
3. If all 390 rows complete, invoke the independent auditor exactly once.
4. Preserve raw, audit, checkpoint metrics, and hashes, then stop the private server.

Identity mismatch before generation is STOP with zero calls. Any call error, interruption, identity change, or incomplete rows is STOP/INCOMPLETE without retry. Any audit error or non-PASS_METHOD status is FAIL_METHOD. A clean audit plus a consistent >=0.10 paired exact-answer contrast across all three seeds yields only a scoped cadence-sensitivity result for this synthetic fixture and model; it does not establish GUI/product effectiveness. The numeric endpoint threshold is inherited from A13's frozen cadence protocol.
