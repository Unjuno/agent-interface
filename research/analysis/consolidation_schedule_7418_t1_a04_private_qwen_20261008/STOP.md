# T1 A04 terminal STOP — invalid consolidation JSON (2026-10-08)

**Disposition: `STOP_INVALID_CONSOLIDATION_JSON`; no scientific result.** The frozen candidate was invoked once and exited 1 after 61 model calls. The first formal request warmed the private Qwen3:8B runner; all tag and loaded-runner identity checks remained at the frozen digest for recorded rows. The failure occurred while parsing a consolidation response after its raw row had already been flushed. The JSON decoder reported `JSONDecodeError` (line 39, column 6). The independent auditor was not invoked and no retries were made.

- Candidate exit: 1; calls: 61; auditor: 0; retries: 0.
- Raw: 61 rows, 308767 bytes, SHA-256 `f9270f529b167e7bb3001fe00a10c0668ef2e145b65734ecd4aaba7d71f9043a`.
- Candidate stdout SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Candidate stderr SHA-256 `d2e1c7c0c6c51fdb6a5ad864e2e7c7e0cc7d31986ebe2dd235aa246072115e97`.
- Frozen package and run record remain; raw and logs are preserved.

Do not resume, repair, score, or rerun this allocation. Its partial output is not pooled with A01–A03 or any future allocation. A future experiment requires a new allocation and fresh seeds.
