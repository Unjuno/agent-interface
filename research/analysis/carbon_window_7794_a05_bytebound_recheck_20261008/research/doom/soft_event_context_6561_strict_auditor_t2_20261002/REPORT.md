# Soft-event strict auditor T2 — scoped result

**Disposition:** `PASS_T2_STRICT_AUDITOR_SCOPED`; independent raw audit: `PASS_INDEPENDENT_RAW_AUDIT` (0 errors).

**H.** A raw-only auditor anchored to an out-of-band binding and the complete frozen `SOFT_CHANGED` receipt contract will accept a complete control and reject the declared binding/authority/decision corruptions.

**T.** One host-CPU candidate invocation against immutable T1 packet bytes, with a new control fixture adding only the two contract fields omitted by T1. One distinct raw-only auditor process ran only after candidate exit 0. Six cases total: one control and five preregistered mutations.

**D.** Control accepted (1/1); mutations rejected (5/5), each with the expected reason family; separate raw auditor reported zero errors. The independent audit also checked all frozen pre-run hashes and confirmed the retained T1 auditor had accepted its original four corruptions. T1 files/results were not changed or rerun.

**C.** Windows 10 build 26200, CPython 3.11.9, host CPU, finite JSON only. No container/WSLc, Docker, GPU/CUDA, model, GUI, game, or experiment network call. Candidate=1, separate auditor=1, retries=0.

**U.** This does not establish that a production caller supplies a trustworthy external binding, that this data changes a live planner decision, or that there is any gameplay/task effect. It does not satisfy the separately gated WSLc allocation or #59 live threat-control requirement.

See `T2_SPEC.json`, `PRE_RUN_SHA256SUMS`, `results/t2-20261002-01/`, and `EXECUTION_RECEIPT.md` for frozen identities, raw packets, decisions, and hashes.

