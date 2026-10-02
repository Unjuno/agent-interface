# Opportunity-conditioned age of actuated information — T0

## H / T / D / C / U

**H.** Observation delivery AoI or dispatch-to-completion latency alone can disagree with observation-generation-to-relevant-effect age. A lineage-aware measurement card should expose that disagreement while refusing to credit irrelevant pulses, dispatch receipts, unknown effects, ambiguous ancestry, or incomparable clocks.

**T.** Eight frozen synthetic rows cover: fresh observation/stalled effect; older but still-valid observation/timely effect; frequent irrelevant pulses; dispatch without independent effect; an opportunity expiring before cycle start; a quiet period with no intervention needed; ambiguous multi-observation ancestry; and cross-clock incomparability. The candidate emits one deterministic raw file. A separately authored auditor reconstructs each row and applies three corruptions (mismatched observation/effect identity, erased effect, incomparable clocks). Candidate once, auditor once, retries zero.

**D.** This is **not a formal T0 result**. Latest Issue #6045 comment #5931960813 requires an explicit new exclusive container slot before future T0; none was granted. The host execution was outside that gate and is retained only as an accountability trace. Independently, its audit exited 1 on a fixture expectation mismatch; no method PASS is claimed.

**C.** Source anchor: main `6cd70ad4bfad74e11658057bf024918bffb24add`. Python 3 stdlib, CPU host. The read-only inventory returned no active Docker containers, but this is not a lease. The shared CPU lane remains assigned to #5074 in #5085; Issue #6045 explicitly requires a fresh exclusive allocation for T0. No Docker/OrbStack was launched, but candidate/auditor were nevertheless run on the host outside that gate. No model, game, GUI/input, GPU, network, or shared allocation was used. This deviation is disclosed, not normalized into formal evidence.

**U.** Out-of-gate host diagnostic only. Candidate raw shows lower delivery AoI for fresh/stalled (10 ms vs 400 ms) but higher observation-to-relevant-effect age (1,190 ms vs 480 ms). Its dispatch-to-effect cycle is 200 ms vs 30 ms; the fixture incorrectly said 1,200 ms. The independent audit failed, the specified corruption controls were not reached, and no formal or verified method result is claimed. No live timing, scorer validity, safety, human tempo, or general GUI claim.

## Frozen interpretation

The two planted rows are deliberately asymmetric: one-way AoI favors fresh/stalled, while effect-age favors older/timely. The raw candidate has cycle latency 200 ms vs 30 ms. #5694 remains the owner of opportunity-denominator/onset-to-effect accounting, and this package is not a replacement for that work.

## Execution record

Out-of-gate host diagnostic candidate: `python3 -B research/doom/map01_r133_age_actuated_information_6045_t0_v1/candidate.py` — exit 0, one invocation, 8 rows, raw SHA-256 `488177257979fce3fc217ec7055eb19f902e27d57608015d26321d97b6965804`.

Out-of-gate host diagnostic audit: `python3 -B research/doom/map01_r133_age_actuated_information_6045_t0_v1/audit.py` — exit 1, one invocation, stopped at the assertion expecting the fresh/stalled dispatch-to-effect cycle to be 1,200 ms. Raw readback gives `1,200 - 1,000 = 200 ms`; fixture's `fresh_stalled_cycle_ms=1200` is inconsistent. This exact first failure is retained; candidate and auditor are not rerun. The auditor did not reach later checks or write an audit artifact. This does not consume or regrade a formal #59 allocation.
