# Issue #6319 allocation 08 — duplicate-allocation STOP

**Disposition: `STOP_PRE_CANDIDATE_DUPLICATE_ALLOCATION`; candidate=0, auditor=0, CUDA calls=0, retries=0.**

This branch contains a pre-run six-worker CUDA memory-sharing proposal using seed `49720261008`. Issue #6319 records that the allocation/seed collided with concurrently registered Issue #6322 allocation 08. The candidate was stopped before launch; this is not a test of the memory-sharing hypothesis and has no scientific PASS/FAIL result.

The separately merged #6322 allocation-08 package is a different experiment (transfer-inclusive latency), despite sharing the seed. Its STOP must not be substituted for this branch's source. The later memory-sharing successor is Issue #6329 allocation 09 with a fresh seed and its own source/runtime/resource gates; this allocation does not authorize or supply evidence for that successor.

The six proposal files are retained exactly as found, including their original paths and content. They were not frozen as a formal allocation in this branch, so do not execute the included commands as a current protocol; any future work requires a new allocation and current-source review. Original source commit: `4bcb2c53823f7d42e2436a58a222da29ef373a72`.
