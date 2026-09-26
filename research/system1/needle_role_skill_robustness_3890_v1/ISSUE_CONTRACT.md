Successor to #3890 / #3780. Preserve all predecessor source, results, auditor chronology, and scoped-PASS wording unchanged. #3890 passed on three seeds, but seed 3789 / role C scored 0.900635 against a 0.90 threshold; its report explicitly recommends a separately preregistered robustness follow-up. This tests fresh-seed repeatability, not a rerun, threshold relaxation, or model promotion.

## H / T / D / C / U

**H — hypothesis**
The versioned JSON role-skill package and receipt-gated A→B→C graph remain competent and exactly reloadable across fresh training seeds; the narrow #3890 role-C pass is not representative of the seed distribution. The experiment may pass or fail this hypothesis; it must report all seeds and role scores without replacement.

**T — allocation**
- Allocation: `needle-role-skill-robustness-3890-v1`.
- Branch: `research/needle-role-skill-robustness-3890-20260926`.
- Additive path: `research/system1/needle_role_skill_robustness_3890_v1/`.
- Base main observed before allocation: `5dd2b9b18fc5f3e73e8ff9adf808806a49a121ce`.
- Use ten fresh deterministic seeds `3792, 3892, 3992, 4092, 4192, 4292, 4392, 4492, 4592, 4692`; do not reuse construction or formal seeds from #3778/#3780/#3890, nor any LoRA seed. The 100-point spacing prevents the retained `seed+1` through `seed+12` component-stream map from reusing a component RNG seed across adjacent formal seeds.
- Keep #3890's three-role synthetic family, 8-feature/hidden-16 tanh core, rank-2 output adapters, A base pretraining (512 examples/400 AdamW steps), separate B/C support adaptation (16 rows/120 fixed steps each), held-out evaluation (4,096 rows per role), JSON-only inert package, content/tensor hashes, two isolated fresh loader processes/containers, and receipt-gated A→B→C lifecycle unchanged. Exact parameters, source provenance and evaluator semantics must be reconstructed from merged #3890 main artifacts and pinned in the new freeze; any ambiguity is HOLD, not inferred.
- For every seed, require both loaders to match builder predictions row-for-row for all 12,288 held-out rows, verify exact package digest and immutable bytes, exercise the valid graph in two fresh generations, reject old-generation receipts, and retain the existing malformed-package / invalid-edge / invalid-scope / duplicate / unverified-receipt controls. Every refusal must leave cursor/package unchanged with zero fixture emissions.
- Freeze source, independent auditor, tests, exact issue-contract text/hash, image digest, seed schedule, output transport, and exact Docker commands before a single formal orchestration. Construction tests must not train. One formal allocation only: no retry, tuning, replacement seed, or post-result exclusion.

**D — decision**
- `PASS_ROLE_SKILL_ROBUSTNESS_SCOPED` only if all 10 seeds and all 30 role/seed cells have held-out accuracy ≥0.90; both clean loaders exactly reproduce all 12,288 predictions per seed; artifact hashes/immutability and graph generation/receipt semantics pass; all negative controls fail closed without mutation/emission; and the independent audit reports zero errors.
- `FAIL_ROLE_SKILL_ROBUSTNESS` for any preregistered competence/reload/graph-integrity miss. Report per-seed and per-role metrics, minimum and distribution; do not average away a failed cell.
- `HOLD` for source/contract/provenance ambiguity or audit defects; typed `STOP` for unavailable Docker/image or evidence capture failure. No model is promoted by this component result.

**C — constraints**
Use cached `needle-pilot05:local` with the exact #3890 image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU-only, deterministic PyTorch, network none, read-only root/source/package, isolated builder and loader containers, dedicated outputs and bounded CPU/memory/pids/tmpfs. No provider, GUI/input, real effect, runtime authority, image pull, Docker repair or cleanup. Record any unavailable-image STOP and do not substitute another image.

**U — limits**
Ten new seeds still sample one synthetic hand-authored three-role family and fixture receipt oracle. This does not establish real Astra teaching, realistic skill transfer, hostile-artifact authenticity/security, cross-device portability, concurrent adaptation/inference, production latency, user-facing skill marketplace behavior, real application effects, or execution authority. SHA-256 is integrity evidence, not a signature.

**Roadmap**
Read merged #3890 source/evidence → verify source and collision state → reconstruct contract without changing predecessor artifacts → construction-only Docker tests → freeze and public readback → one ten-seed builder/two-loader Docker allocation → independent audit/corruption tests → evidence-only PR → CI/review → merge scoped evidence to main → close with immutable PASS/FAIL/STOP. Global ROADMAP remains open.
