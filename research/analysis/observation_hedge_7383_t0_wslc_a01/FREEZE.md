# Issue #7383 T0 — allocation 01

Status before formal run: frozen; no candidate/auditor container invocation yet.

## Identity and provenance

- Allocation: `OBSERVATION-HEDGE-7383-T0-WSLC-20261004-01`.
- Repository intake main: `13bab54ea6d91978247ecc1b70e5060db752367a`.
- Additive branch: `research/observation-hedge-7383-t0-wslc-20261004`.
- Additive path: `research/analysis/observation_hedge_7383_t0_wslc_a01/`.
- Candidate SHA-256: `dd0cdea25f5706a30e4844a376502e0f5f59a0b5938aeb0dddafe1d9a4a7062`.
- Independent auditor SHA-256: `ba03088faa733490d9567915c35d6bbf10d8cf4a1ba4c2768210d84af5af02eb`.
- Freeze SHA-256: `6be5534b1c9576f454e1f30802ac059aeab96f1da3f34e98ffc8537ec3207642`.
- Runtime: WSL 3.0.1.0 / WSLc 3.0.1.0; Linux `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, amd64, Python 3.12.14 in image.
- Network disabled; source read-only; separate writable output; one CPU requested; memory 512 MiB requested. Any cgroup/swap warning will be preserved; effective memory enforcement is not claimed.
- Existing WSLc container inventory was read immediately before freeze: no running containers. No existing/stopped container or image will be changed or removed.

## H / T / D / C / U

**H.** On a frozen heavy-tail read-only observation workload, one delayed secondary request at the 90th-percentile service time of a disjoint calibration set reduces complete-current-observation p95 by at least 10% versus one request while mean total service work stays at or below 1.5× baseline. Under correlated delay, shared-queue perturbation, cancellation lag, or a generation change, benefit may disappear or freshness may prevent admission.

**T.** The candidate deterministically evaluates 40 authored rows in each of five strata: `heavy_tail`, `correlated`, `shared_queue`, `cancel_lag`, and `generation_flip`. Three arms are `single`, `delayed` (one secondary only if primary has not completed by threshold), and diagnostic `immediate`. Calibration is the frozen 20-value tuple embedded identically in candidate/auditor; threshold is the nearest-rank p90 (11 ms). The candidate records all 600 arm-rows, response completion/currentness/epoch, winner and service-work accounting. A separate implementation reconstructs every row and replays four integrity corruptions.

Workload rules are fully encoded in the frozen source: heavy-tail primary service is 80 ms for every tenth case and 3–9 ms otherwise; correlated secondary is one ms slower than primary; the shared-queue stratum adds eight ms to primary service only when a duplicate is launched; cancellation-lag cases add the authored 8–16 ms cancellation delay to loser work; generation-flip changes source generation at 3 ms. A response is admissible only if complete and its captured generation equals the generation at completion. It never grants actuation authority.

**D.** `PASS_METHOD_SCOPED` requires exact 600-row independent reconstruction and rejection of partial-response, stale-generation-first, double-admission and omitted-loser-work mutations. `H_PASS_SCOPED` additionally requires heavy-tail p95 reduction >=10% and delayed-arm mean work <=1.5× single-arm mean. These are authored finite deterministic cases, not real capture latency. Report other strata separately, including invalid/unavailable observations in denominators; do not generalize to actual GUI systems.

**C.** A single capture worker/compositor may serialize or correlate requests; cancellation may be slow; any apparent advantage may be specific to the authored heavy-tail distribution. Piggybacking, nonredundant caching or simply using one read may dominate outside the planted region.

**U.** No real X11/Xvfb capture, GUI mutation, model, user desktop, action, GPU, externally measured latency distribution or live task effect is included. The p90 threshold and five 40-row strata are authored, finite values. WSLc memory-limit enforcement is unknown. This cannot establish actual critical-path position or task-level benefit.

## One-shot limits

One candidate invocation and one independent auditor invocation, no retry, no tuning and no replacement rows. Immediately before candidate invocation, re-fetch main and compare any intervening changes against the experiment contract/source; stop if a change invalidates the frozen question, safety/currentness contract, or source identity. Unrelated additive main changes are recorded without rebasing or silently altering this frozen allocation. Candidate/auditor outputs go only to the separate output mount. Source and gates are not edited after this freeze.
