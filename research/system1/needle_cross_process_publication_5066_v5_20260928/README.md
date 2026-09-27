# Issue #5082 Stage 0 protocol design

This scratch is not yet the frozen experiment bundle and has produced no atomic-publication result.

## H / T / D / C / U

**H.** On one local Linux filesystem, four independently identified reader processes repeatedly open, read, hash, and validate a fixed active package while one publisher performs exactly 4,096 same-directory `os.replace` calls. Every completed read is either a complete expected generation or a fail-closed read; at least 32 reader open-call intervals positively overlap replacement-call intervals across at least two PIDs. A barrier-controlled truncate/partial-write diagnostic must be observed as invalid partial bytes by all four reader processes.

**T.** Fresh allocation `needle-cross-process-publication-overlap-5066-v5-20260928-01`, Issue #5082, additive branch `research/needle-cross-process-publication-overlap-5066-v5-20260928`, path `research/system1/needle_cross_process_publication_5066_v5_20260928/`. Earlier proposed v3 was already stale at `d739d70…`; our empty v4 ref was based on `34e42f84…` and is preserved. Current main at this construction freeze is `8f41a5edba1acda9dcecfc4fb91cea5186b78087`. Input is the exact seed-3788 Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107`, 15,279 bytes. Do not copy its normalized/text-transformed form as if it were the original Git object. Image: cached `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64. One runner process orchestration and one separate raw-only audit orchestration; no retries.

Every reader attempt records PID, index, monotonic `open_start_ns`, `open_end_ns`, bytes, observed generation, package SHA-256, parse/validation outcome, and error. Publisher records all 4,096 replacement-call start/end intervals and expected generation/hash. Half-open interval overlap is `max(starts) < min(ends)`. Count qualifying reader calls, not reader×replacement pairs. Require exactly indices 0..4095 and >=32 unique reads across >=2 distinct reader PIDs. Readers must acknowledge readiness before publication begins. A zero-overlap result is `HOLD_NO_OVERLAP_OBSERVED`, never a pass.

The diagnostic uses a separate fixed schedule: truncate active, write and flush the first half, signal a barrier, have all four reader processes open and retain the observed partial bytes/hash before the publisher writes the remainder. No tuning from observed data. Preserve both complete and partial outcomes.

**D.** `PASS_ATOMIC_REPLACEMENT_OVERLAP_SCOPED` only if complete raw data reconciles, all 4,096 publications and all reader attempts are present, overlap coverage threshold passes, every complete atomic-arm read is one exact expected valid generation, each diagnostic reader exposes invalid partial bytes, independent audit has zero errors, and every corruption control rejects. Valid but zero-overlap is HOLD. Accepted torn data is FAIL. Missing provenance/process/audit is HOLD/STOP.

**C.** Local Docker Desktop only, Linux/amd64 container; network none, image pull never, source/root read-only, bounded CPU/memory/PIDs, fresh output. Synthetic inert JSON only; no model, GPU, credentials, GUI, dispatch, or authority. Never alter sibling containers. The #5074 owner is currently using Docker for construction checks, so no container launch from this lane until explicit resource release.

**U.** One host, one local Linux filesystem, CPython scheduling, one synthetic package. Call-interval overlap does not reveal kernel-internal linearization. Fixed directed concurrency is not a natural-race rate, durability, cross-filesystem behavior, production safety, model utility, or performance claim.

## Known external state

- #4986 Stage 1 tested four reader threads in one process and observed construction-level atomic/in-place behavior; that is related evidence, not a duplicate of this fresh process-overlap question.
- #5066 post-merge review found its atomic readers completed before replacement and frozen source hashes disagreed with Git bytes. Preserve its PASS/raw/branch unchanged; #5082 is the fresh successor.
- Local pure helper/full raw-auditor fixture tests: 8/8 pass. These test arithmetic, raw reconstruction, and mutation rejection only; no actual process concurrency was run.
- Formal Docker slot currently belongs to another active lane. No output path is created and no formal invocation has occurred.
