Fresh successor to #4529 / #4479 / #3890. Preserve every predecessor byte and outcome. #3890 established one scoped synthetic role-skill lifecycle PASS on seeds 3788–3790, with role C as low as 0.900635. #4479 formally STOPped before training due missing Docker environment bindings; an independently launched conflicting attempt also STOPped before container start. No model was trained by either #4479 attempt. #4529 documented the freeze/contract discrepancy and explicitly requires a new successor when it cannot be reconciled. This Issue does not retry either consumed orchestration.

## H — hypothesis
The exact #3890 role-specific adapter graph will meet its per-role >=0.90 held-out accuracy floor across a genuinely fresh ten-seed block, with two exact cross-process reloads and generation-bound A→B→C receipt semantics for every seed.

## T — frozen scope / allocation
Allocation: `needle-role-skill-robustness-3890-v3-freshblock`.
Additive path: `research/system1/needle_role_skill_robustness_3890_v3/`.
Branch: `research/needle-role-skill-robustness-3890-v3-20260927-01`.
Current main at intake: `a1a9a7d0abdcdf65d5aba3b74e7f7caf171f2ca4`.

Use fresh seeds `913000, 913100, 913200, 913300, 913400, 913500, 913600, 913700, 913800, 913900`. Preserve #3890's synthetic three-role family, 8-feature/hidden-16 tanh core, rank-2 output adapters, A pretraining (512 rows/400 AdamW steps), B/C adaptation (16 rows/120 fixed steps), and 4,096 held-out inputs per role. No architecture, task, optimizer, support, schedule, score threshold, or graph change. This is a newly preregistered robustness allocation, not #4479's retired/conflicting schedules. Construction must programmatically prove this seed block and each seed+1..seed+12 stream is disjoint from #3890 seeds 3788–3790 and #4479 candidates 3792..4692 / 100000..100900, and must assert unique per-seed output paths.

Adapt the immutable merged #3890 code, freeze exact source and contract hashes, and preserve all predecessor files. Fix #4479's demonstrated harness gap: before freeze, a construction-only test must assert Docker builder argv supplies both `NEEDLE_SEED` and `NEEDLE_OUTPUT` exactly as `runner.py` reads them, and missing/invalid environment fails closed before training. Use only cached `needle-pilot05:local` image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, CPU-only, one thread, network none, read-only root/source/package, 1 CPU/2 GiB/64 PIDs/64 MiB tmpfs, dedicated writable per-seed outputs. No image pulls, package installs, GPU, network/provider, GUI/input, user data, live effects or execution authority.

One formal Docker orchestration only, ten seeds, no retries, tuning, replacement, post-result exclusions or seed reselection. For each seed retain builder package/tensors/raw expected predictions, two isolated loader results and package-before/after digests, stdout/stderr/exit receipts and timing/resource data. Independent audit must independently regenerate labels and logits from retained tensors/inputs (no importing runner, loader or formal orchestrator), verify exact raw/package/source identities, all 12,288 predictions per loader, controls and per-role metrics. Retain corruption controls with changed-byte proof.

## D — decision
`PASS_ROLE_SKILL_ROBUSTNESS_SCOPED` only if all 30 seed×role accuracies >=0.90; both fresh loaders exactly match all 12,288 builder predictions for each seed and bind to that seed's exact package digest; package bytes remain immutable; valid generation-current graph transitions pass; stale-generation, tampered/malformed package, invalid edge/scope/version/receipt, duplicate receipt and unverified outcomes fail closed without state mutation/emission; and an independently implemented audit has zero errors.

Any quality or lifecycle gate miss is `FAIL_ROLE_SKILL_ROBUSTNESS`. Auditor/provenance defects are `HOLD_AUDIT_OR_PROVENANCE`. Missing cached image/environment or output capture is a typed `STOP`, not a scientific result. No runtime/model promotion follows.

## C — competing explanations
The prior three-seed pass may be representative and the marginal low role-C seed may be sampling noise; or role-C may be near the threshold and fail under fresh seeds. Exact reload/receipt integrity does not imply useful real-world skill. Failures can also arise from orchestration/evidence binding and must remain distinct from model quality.

## U — limits
Ten seeds sample one synthetic hand-authored three-role family and one local CPU image. No evidence for Astra teaching, natural task skill transfer, arbitrary GUI, production latency, hostile artifact authenticity, concurrent training/inference, user utility or execution authority. SHA-256 supplies integrity, not authentication.
