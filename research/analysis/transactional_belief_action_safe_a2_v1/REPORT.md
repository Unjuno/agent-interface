# #1825 — Transactional belief ACTION_SAFE A2

Decision: **PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_A2_SCOPED** with **PASS_AUDIT**.

Successor to #1817. The predecessor construction failure remains unchanged; its formal count stays 0. This A2 changes only construction eligibility: the length-8 fresh-recommit witness is checked directly during construction, while the formal discriminator remains exhaustive through depth 8.

## H/T/D/C/U
- **H** — durable COMMITTED provenance can persist across generation change, but ACTION_SAFE is freshly derived from current COMMITTED support, exact support/current generation equality, and no contradiction.
- **T** — source-frozen deterministic Python stdlib state machine; seven-operation alphabet; every trace length 0..8; candidate vs separately implemented oracle; sticky-COMMITTED comparator; independent re-enumeration; four corruption controls.
- **D** — PASS requires mismatch0, stale/contradicted ACTION_SAFE0, unvalidated COMMIT0, fresh recommit>0, retained provenance>0, comparator unsafe discriminator>0, exact independent digest/metric agreement, source integrity, formal1/reruns0.
- **C** — a one-claim finite lifecycle does not establish multi-support truth maintenance, uncertainty/trust semantics, derived-claim repair, concurrency, or runtime integration.
- **U** — analytical container model only; no GUI/X11/model/provider/network/task input, token, latency, or product claim.

## Formal result
- exhaustive traces including empty: **6,725,601**; transitions: **6,725,600**;
- candidate/oracle mismatches: **0**; identical digest `56f1f3ac759f9715b9934a587f1094017222796e5b1dc1835c4bc482e26b7387`;
- stale-generation ACTION_SAFE admissions: **0** across **4,044** stale opportunities;
- contradicted ACTION_SAFE admissions: **0** across **6,782** contradicted opportunities;
- COMMIT-from-unvalidated admissions: **0** across **851,830** attempts;
- valid fresh recommit ACTION_SAFE witnesses: **4**;
- retained commit-provenance observations across generation advance: **26,598**;
- COMMITTED_ONLY unsafe stale/contradicted admissions: **10,826**; total comparator unsafe admissions: **25,878**.

The independent auditor re-enumerated the same **6,725,601** traces without importing candidate helpers and produced the same digest. All four corruption controls were detected and all source hashes matched the freeze.

## Execution integrity
- formal invocations: **1**; reruns: **0**; replacements: **0**; post-freeze tuning: **0**.
- source SHA-256: formal `a4ec5b5255926db908eb60b4452bae4842a88e4030a7d96a77125b6d06198868`, audit `6673088b2727095fc55aa484ba3eaf8cb78d742adbdaeb2bb754d64269a7e8b1`.
- execution host (non-benchmark metadata): Python 3.13.5, Linux 6.18.44 x86_64, AMD EPYC 9V74. Formal enumeration elapsed 11.901 s; this wall time is not a performance claim.

## Interpretation
Within the frozen finite model, COMMITTED and ACTION_SAFE are not equivalent. Keeping a durable commit record while re-deriving action admission from current support prevents the stale-generation and contradiction leaks exposed by a sticky commit-only authority rule. The result is a scoped semantic prerequisite, not an integrated runtime promotion.
