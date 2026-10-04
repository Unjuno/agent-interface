# Issue #6089 T0b — scheduled-observation erasure extension

## H / T / D / C / U

**H.** If an already-authorized bounded motor program reaches its scheduled observation time but no current source-bound observation is actually delivered, assuming success can extend stale input into an unsafe prefix. Releasing at the first absent/stale checkpoint is the safe default. A separately computed loss-robust horizon may allow longer use of the same authorization only when every in-envelope disturbance prefix remains safe through the declared burst of missed checkpoints and the worst-case release lag.

**T.** Seven deterministic finite one-dimensional cases compare: A, a policy that assumes a scheduled observation arrived; B, release on the first absent/stale checkpoint; and C, an independently bounded loss-robust horizon. Cases include no-loss / k=0, a planted unsafe optimistic extension, a two-miss in-bound burst, an old-generation delayed receipt, target invalidation, loss beyond the declared bound, and unsupported loss bounds. Candidate propagates reachable sets. A separate raw-only auditor recursively enumerates state/disturbance paths for each possible missed-checkpoint count and checks every prefix and release completion.

**D.** `PASS_METHOD_SCOPED` only if the no-loss loss-robust horizon exactly equals the original no-loss horizon; A exposes the planted unsafe continuation; B releases on absent/stale input and remains within the fixture's release gate; C admits no unsafe prefix for any in-bound erasure count up to frozen k; stale generations never count as fresh; invalidation and unsupported bounds yield; the beyond-bound case is labeled uncertified; and all five raw-result corruptions are rejected by the independent auditor. Any false in-bound safety result is `FAIL_UNSOUND_LOSS_ENVELOPE`.

**C.** Release-at-first-absence may dominate the more complex C continuation. A reliable independent capture channel may make missed checkpoints rare. The finite plant and stipulated burst bound may be easier than real correlated observation failures.

**U.** This does not justify a loss bound for any GUI, game, model-delivery channel or host. Bursts may correlate with focus changes, app freezes, overload or stale source generations. Synthetic PASS is neither live input authority nor a GUI/DOOM safety claim or performance gain.

## Frozen semantics

- State: integer position; each slot is `x' = x + action + disturbance`.
- Legal in-envelope disturbance set: `{-1, 0, +1}` per slot; all initial states and all prefixes are enumerated.
- A fresh receipt must match the current source generation and have age within the frozen maximum. Missing and stale-generation receipts both consume one eligible loss slot; stale feedback never refreshes authority.
- On first no-receipt deadline, B starts release. C may continue only the already-authorized action through at most k missing checkpoints, then releases by the bound deadline; it cannot choose a new target/action.
- A target invalidation forces immediate YIELD for every arm. Unsupported loss bounds disable C and require YIELD.
- Out-of-bound stress is descriptive only and is never called certified.

## Execution

Allocation: `OBS-LOSS-ROBUST-TUBE-6089-T0B-HOSTCPU-20261002-01`. Branch: `research/observation-loss-robust-tube-6089-t0b-20261002`. Base main is recorded in `FREEZE.json`. Bounded window: 2026-10-02 08:32–08:40 UTC. Owner: current Unjuno autonomous research task on this Windows host.

Host Windows CPython 3.11.9, stdlib only; no model, GPU/CUDA, training, adapter update, Docker/WSLc container, network, GUI, game, or user input. Construction tests precede freeze. Candidate and independent auditor are each allowed one fresh, non-colliding output invocation; retries/replacements are zero. Final start gate requires current main == `FREEZE.json.base_main`, exact source hashes, and both output paths absent. Any mismatch is STOP before candidate; candidate nonzero means no auditor run.
