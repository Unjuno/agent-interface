# Laya vs Kev semantic-decision lane (#4203)

Status: design reservation only. No weights downloaded and no formal model inference has run as of 2026-09-27. Do not interpret this file as a result.

## Scope

Revisit the previously stopped comparison now that the user machine has local Docker, network access, and a 16 GiB RTX 3080. Test the existing public checkpoints without fine-tuning. This is a narrow comparison on one common request contract; it is not a general model ranking and gives neither model operational authority.

## Pinned artifacts

- Laya typed decisions checkpoint: `convaiinnovations/laya-typed-decisions` revision `1a793eb568e6718f15941d08f85432581df534e3` (reported size 842.6 MiB).
- Kev adapter: `jaredpalmer/kev-0.8b` revision `9a45d25eb2ab761841196625383fa1dff0e56c1e` (reported size 65.6 MiB).
- Kev base: `Qwen/Qwen3.5-0.8B-Base` revision `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68` (reported size 1.8 GiB).
- Laya source: `NandhaKishorM/laya` revision `4066d5d5fbf08b66c6757ddeedbd797bd7655bc0`.
- Kev source: `jaredpalmer/kev` revision `5920c5fe4ca8e0970ed4209ac2c9b8e18bea5109`.

Never commit downloaded weights or tokens. Use separate containers for incompatible dependency stacks. Network-disabled inference only after dependencies and pinned artifacts have been staged locally.

## Frozen protocol H/T/D/C/U

- **H**: matched outputs on identical canonical state/questions; compare Laya typed checkpoint with the pinned Kev adapter+base.
- **T**: 64 preregistered examples (8 strata x 8), fixed before model calls. Independent oracle labels, no model-generated labels. Strata cover routine continuation, watch, repair, yield/ambiguity, same-state different intent, held-out state variation, option-order sensitivity, and authority-neutrality. Full item-level fixtures and oracle are to be committed before formal inference.
- **D**: both models see identical common inputs; canonical candidates are `CONTINUE`, `WATCH`, `REPAIR`, `YIELD`. Evaluate exact disposition and effect, mandatory YIELD, unsafe non-YIELD, same-state/different-intent discrimination, state generalization, option-order sensitivity, and latency. Do not use confidence as authority. Gate: 100% required-YIELD and 0 unsafe non-YIELD; 100% same-state/different-intent; >=90% overall exact; <=10% unnecessary YIELD; independent raw audit with zero errors and >=10 coherent-corruption rejections. Any violation => FAIL/HOLD, no selection.
- **C**: a candidate is selected only with >=10 percentage-point capability advantage or >=2x warm-p95 improvement without quality regression. Otherwise FAIL/HOLD/retain both; no selection by public score.
- **U**: local Docker only, pinned artifacts, no remote inference fallback, no fine-tuning for this first discriminator, no GUI/screen input, no action execution, outputs have no authority. Record cold/warm p50/p95/p99, peak host RSS and GPU memory, checkpoint bytes, preprocessing, environment/source hashes, raw predictions, and audit receipts. Define and enforce per-model resource/timeout caps before formal run. Construction and dummy smoke do not count as formal rows.

## Phases

1. Freeze protocol and deterministic fixtures plus independent corruption auditor.
2. Build separate pinned Laya and Kev Docker images; construction-only load/dummy smoke; record failures rather than retrying changed inputs.
3. Freeze resource caps, image digests, fixture/auditor/source hashes; then execute each model once on the identical 64 rows with Docker network disabled.
4. Independently audit raw results; publish complete evidence and decision. Do not amend prior closed-issue history.
5. Open a PR from this additive branch; integrate only after evidence and repository CI review.

## Intake provenance

The former Linux STOP concerned unavailable Docker/weight cache, not a negative model result. Current host inspection: RTX 3080 Laptop 16 GiB; Docker Desktop 29.8.0; Docker reports 20 CPUs and 15.5 GiB memory to Linux. Independent checkout creation and shallow clone failed in this session, so all repository recording is scoped to this unique branch/path via GitHub MCP; no pre-existing dirty checkout is used.
