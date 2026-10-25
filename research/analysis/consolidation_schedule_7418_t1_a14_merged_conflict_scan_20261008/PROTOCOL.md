# A14 protocol

## Question
Under the fixed six-episode synthetic fixture, does explicitly directing the model to rescan the complete merged memory for fact conflicts address the repeated batch-boundary omission seen in A12/A13, while preserving claims and transition structure?

## Allocation and arms
- Allocation: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A14-MERGED-CONFLICT-SCAN-20261008`.
- Independent seeds: 5401, 5402, 5403.
- Arms: episodic-only, per-episode, batch-of-two, terminal-only; rotation is fixed in the runner.
- Prefixes: 1 through 6. Five fixed queries per prefix.
- Planned calls: 360 queries plus 30 consolidations = 390.
- Model: `qwen3:8b`, frozen digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`.
- Server: private Ollama instance on `127.0.0.1:11435`; dedicated model store `/tmp/unjuno-8406-t1-a14-ollama-store`. Do not use or modify the shared default Ollama server.

## Controlled intervention
Relative to A13, only `prompts.json` changes: consolidation explicitly applies two passes, first preserving prior claims and adding one claim per new episode, then scanning all fact observations in the full combined set (old and new) for same-key/scope differing values and ensuring the corresponding conflict claim exists. The schema constraint and all other run controls are held fixed. Fresh seeds distinguish the allocation; no historical rows are pooled.

## Execution
1. Freeze and publish the manifest/preregistration before model generation.
2. Verify the private tag and every manifest blob against the frozen digest; save preflight JSON and checksum.
3. Invoke the candidate runner exactly once. Do not retry any failed, truncated, or ambiguous call. Preserve every written raw row.
4. Only if all 390 rows are present, invoke the independent auditor exactly once. Preserve the audit output and checksum.
5. Stop the private server after raw and audit artifacts have been saved.

## Stop and interpretation rules
- Identity/tag/blob mismatch before generation: `STOP`; no model calls.
- Any runtime error, interruption, truncation, unexpected identity, or row count other than 390: `STOP/INCOMPLETE`; no retry and no independent audit unless all 390 rows exist.
- Auditor errors or status other than `PASS_METHOD`: `FAIL_METHOD`; endpoint accuracy/arm contrasts remain descriptive and do not support a schedule conclusion.
- `PASS_METHOD` with zero errors: report per-seed and aggregate contrasts descriptively with limitations; this small synthetic fixture does not establish GUI task effectiveness or user benefit.
- Never unload, delete, overwrite, or repool another allocation's store or artifacts.
