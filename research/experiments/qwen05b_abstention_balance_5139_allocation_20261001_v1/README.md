# Qwen support-balance allocation — 2026-10-01

Fresh additive successor for Issue #5139. This package is isolated from and does not modify the immutable #4988/#5014/#5139 predecessor artifacts.

## H / T / D / C / U

- **H:** With an equal 32-row support budget, the same Qwen2.5-0.5B-Instruct base, LoRA setup, optimizer, 16 updates, parser/binder/simulator, and common 64-row held-out set, balanced 4-per-class support will improve exact semantic action/effect quality and abstention safety over the predecessor-shaped 16/4/4/1/1/1/1/4 support mix.
- **T:** Allocation `QWEN-SUPPORT-BALANCE-5139-20261001-01`; Windows local RTX 3080 Laptop GPU and Docker Desktop `desktop-linux` only. Exact bounded resource window: 2026-10-01 08:15–10:15 UTC; earliest candidate start is buffered to 08:20 UTC after the #5752 GPU-only slot ends. Current-main source base observed during preparation: `bd9c4c5ceca68f4dc09bb39d27b140a987b68656`; this is not the launch freeze. Re-freeze against exact main at the reserved start. Generate separate support (128 rows) and held-out (256-row pool, 64 selected) sets with three distinct fresh seeds. Two rank-8 LoRA arms, 16 AdamW updates each; one base and one per-adapter evaluation. Offline, network-disabled, no remote or hosted execution.
- **D:** `PASS_BALANCED_SUPPORT_ABSTENTION_SCOPED` only if the independent raw audit reconstructs all outputs, rejects all five frozen corruption controls, balanced exact action/effect is at least 80% and at least 15 percentage points above both comparators, all eight classes are 8/8 exact, no forbidden/stale/unauthorized simulated effect occurs, balanced p95 is at most 1.2s, each fit is at most 300s, and peak CUDA allocation is at most 12 GiB. Integrity/provenance failure is STOP; resource failure is HOLD; audited quality miss is FAIL. No retries or seed substitution.
- **C:** Only support selection differs between arms; source protocol, pools, held-out bytes, tokenizer/model, formatting, formal seed, LoRA initialization, optimizer and decoding are shared. The independent reconstruction code imports neither the candidate data builder nor its sampler. All mutations and failures are retained.
- **U:** One synthetic seed pair, one cached model revision, one laptop GPU and one simulator. No claim about live GUI actions, production authority, deployed adapters, other hardware/models, or population-level effects.

## Historical lineage and safety

The old `sad_cannon` execution identity, owner and fit count remain unknown and unreconciled; preserve the prior terminal HOLD and do not infer zero prior fits or proven non-overlap. This is a wholly fresh allocation/path/data set and does not reuse old adapters, seeds, formal dataset, or outputs. The unknown predecessor history is reported as a limitation, not rewritten as a cleared result.

The new reservation is a separate, future-dated 2026-10-01 window; it cannot overlap the documented 2026-09-28 predecessor observations. This time separation only isolates the new run. It does not identify `sad_cannon`, recover the old fit count, or clear/rewrite the predecessor HOLD.

## Start gates

Before any Docker, model/tokenizer load, CUDA, fit, or adapter write: verify exact current-main SHA and all source/data/model/tokenizer/image hashes; pass host and pinned-image CPU-only construction tests and preflight; verify seed/path/output collision receipts and empty formal output; confirm the exact bounded owner/resource reservation remains active; require at least 64 MiB free on the host output volume immediately before claiming the one-shot formal attempt; then take immediate read-only GPU/process/container inventory. The runner fails closed below this reserve. Use only a pre-existing exact pinned local image; do not pull/build or use cloud. Any failed gate is preserved as STOP before model load. After the single formal orchestration, run a separate CPU-only raw audit and exactly five corruption controls. Publish evidence by PR.

The pinned CPU suite intentionally combines this allocation's five tests with the current-main protocol and sampler tests only; it omits the predecessor `test_freeze_schema.py`, whose allocation ID/main pin belongs to an older freeze. The suite uses synthetic unit fixtures, not predecessor formal dataset bytes. Run from the read-only mounted `/experiments` tree before preflight:

```powershell
python /experiments/qwen05b_abstention_balance_5139_allocation_20261001_v1/pinned_construction_tests.py
```

Then run `allocation_runner.py --preflight-only` with a separate, unique empty output directory. It verifies hashes and allocation bindings while explicitly recording `model_loaded=false`, `cuda_called=false`, and `fit_invocations=0`. Only after both pass and a fresh inventory may the single formal runner be invoked.

## Frozen fresh seeds

- formal/training seed: `898659560`
- support-ranking seed: `582882955`
- held-out-pool/selection seed: `292197310`

These values were generated for this allocation and exact-searched against all comments on #5139/#5085 and the repository default-branch code search; no exact matches were returned. See `SEED_COLLISION_CHECK.json`. They are distinct from one another and from known prior/test sentinels.

Realized class/template/field counts for both support arms and the held-out pool are in `COVERAGE_SUMMARY.json`. Coverage was measured after the fixed seeds were chosen; it was not used to choose or replace them.
