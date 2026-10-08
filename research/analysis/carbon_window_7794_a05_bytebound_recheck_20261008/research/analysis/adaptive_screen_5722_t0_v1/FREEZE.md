# Issue #5722 T0 freeze — 2026-10-01

## H / T / D / C / U

**H.** In this declared heterogeneous finite world, a balanced safety-gated screen will identify a correctness-preserving candidate that passes a separate sealed matched confirmation with fewer development opportunities than safety-gated equal-full evaluation. An easy-first scalar successive-halving control will falsely eliminate the delayed-recovery candidate. This is a method construction, not empirical Agent Interface performance.

**T.** Frozen world: `world.json`. Four arms (`baseline`, `slow_recover`, `weak`, `unsafe_easy_first`), two strata (`easy`, `hard`), four development variants per stratum, and distinct four-variant sealed confirmation for `baseline` versus `slow_recover`. First-use setup cost is three declared resource units per arm. Policies: (1) equal-full evaluates each arm in matched easy/hard order and stops an arm on a forbidden effect; (2) naive control screens the first two easy cases, retains the top two scalar success counts with lexical tie-break, then probes hard cases with the same safety stop; (3) proposed policy screens every arm on one case from each stratum, immediately stops a hard-safety failure, records screen-eliminated arms as `ELIMINATED_BY_SCREEN` (not inferior), drops an arm only when both pilot strata are zero and baseline is positive in both, then extends the other safe arms across the remaining development variants. The best remaining safe arm is evaluated against baseline on the untouched sealed variants.

**D.** Candidate outcome requires the adaptive policy to use fewer development attempts (excluding equal setup charges), shared setup cost not to erase total resource-unit savings, select `slow_recover`, and pass sealed confirmation: zero forbidden effects, no worse correctness in either stratum than baseline, and strictly greater total correctness. The auditor independently checks exact frozen inputs, per-attempt assignment, safety stops, attempt totals, eliminated-arm labeling, no sealed/development overlap, and the final decision. Mutations deleting/duplicating an attempt, altering safety evidence, reusing a development variant as sealed, or promoting under resource contention must all be rejected.

**C.** Fixed equal matched blocks are easier to interpret and may be preferable when the full candidate set is affordable; screening may discard a candidate that would recover on later tasks.

**U.** The table and delayed benefit are authored, deterministic fixtures. No model, GUI, runtime, task effect, empirical ranking, safety rate, or real shared-resource saving is tested. A screen-eliminated candidate is not proven inferior. The host fallback is not Docker evidence. No live T1 is authorized.

## Frozen execution policy

- Repository main observed at start-gate refresh before source publication: `5ff239141f49c1603c0f6b078268f4a2f6e082df` (main advanced during freeze; the two intervening commits add Issue #5716 workflow-conformance construction and #5692 security STOP evidence, both path-disjoint from this finite simulation).
- Unique work path: `research/analysis/adaptive_screen_5722_t0_v1/`.
- Unique branch: `research/5722-screen-confirmation-t0-20261001`.
- Candidate runner: `runner.py`; independent raw-only auditor: `audit.py`.
- SHA-256: `world.json` `6f74bb9d2d767d3ba6fc066e88b0d22fcf796443c35e9e2a8381d135bdc7466b`; `runner.py` `c05d361e01c47dafc36e4205cf465aaed21f6bf47a44617b2670e9185f4cbcf3`; `audit.py` is pinned by `SHA256SUMS.txt` on the source branch before execution.
- Run each once, sequentially, under Python 3.12.10 on the Windows host because Docker Desktop's Linux engine is unavailable. Runner output must be absent at launch. Auditor runs only after runner exit 0. No retries.
- Candidate stops on first safety violation for an arm. Equal-full comparator follows matched alternating strata. Adaptive development trial budget is compared separately from the new sealed confirmation budget; setup resource units are charged equally to every arm in both policies.
- No network, model, GPU, GUI, X11, game, or input.
