# Preregistration — #4749 role-C support 16 vs 64

## H/T/D/C/U

**H.** Increasing role C supervised support from 16 to 64, preserving the exact first 16 rows and all paired factors, will remove below-0.90 C cells over a fresh ten-seed block, improve paired mean C accuracy by >=0.01, and leave A/B exactly unchanged.

**T.** Allocation needle-role-skill-c-support64-4749-v1; branch research/needle-role-skill-c-support64-4749-v1-20260927-main; additive path research/system1/needle_role_skill_c_support64_4749_v1/. Construction seed 7865001; formal seeds 7865101, 7865201, 7865301, 7865401, 7865501, 7865601, 7865701, 7865801, 7865901, 7866001. Each seed builds paired control16/treatment64 C adapters from the identical A base, initial adapter, support prefix, heldout set, optimizer and 120 steps. Export inert data-only JSON. Run two fresh isolated loaders per package and a separate auditor independently reimplementing training, predictions, package checks and graph protocol without importing trainer/loader/orchestrator.

Image is pinned by immutable ID sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e (needle-pilot05:local, linux/amd64). Containers use no network, read-only root and source/package mounts, one CPU, 2 GiB memory, 64 PIDs and bounded tmpfs. Each seed/arm/loader has a unique output directory. Exactly one formal orchestration; no retry, tuning, seed substitution, exclusion, or retraining.

**D.** PASS_ROLE_C_SUPPORT64_SCOPED only if candidate C has zero cells below .90, paired mean delta >=.01 and candidate mean is not below reference, paired A/B are exactly equal, all package/digest/two-loader/graph/corruption/integrity checks pass, and independent audit has zero errors. Otherwise complete evidence is FAIL_ROLE_C_SUPPORT64; unresolved auditor/provenance is HOLD; environment/evidence failure is typed STOP. Publish every seed pair and distribution.

**C.** Ten seeds have limited power for rare tails. The difference may reflect seed/optimizer or generator behavior rather than support count. Hashes show integrity, not authenticity; synthetic reload is not natural transfer.

**U.** At most this tests synthetic role-C LoRA generalization and inert role-skill portability on one Docker CPU image. It does not establish real-time online training, Astra supervision, concurrent-agent robustness, general task/GUI transfer, production readiness or execution authority.

## Source and allocation boundary

Immutable upstream runner, loader, auditor and preregistration are retained under source/ with #3890 provenance and hashes. New trainer, loader wrapper, auditor, orchestrator, tests and outputs are separate. Construction seed is outside the formal block and consumed only for construction. Formal seed reuse is prohibited.

FREEZE.json is intentionally absent until GitHub source/contract/freeze readback and freeze-time main/issue/collision/branch/image checks pass. This draft does not authorize formal execution.
