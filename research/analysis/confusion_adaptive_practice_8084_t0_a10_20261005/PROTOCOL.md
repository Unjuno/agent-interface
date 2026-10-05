# Issue #8084 T0 A10 — finite overdispersion frontier

## H / T / D / C / U

**H.** Gate qualification may change systematically as between-opportunity pair-rate overdispersion decreases. A finite concentration sweep should show whether the A09 κ=40 STOP is local to that stress or persists toward the fixed-rate case, without tuning or changing the gate grid.

**T.** Use the same eight authored profile means, n∈{20,100}, and 20 fixed span/peak gates. Run five hidden arms: Beta-binomial concentration κ∈{20,40,80,160} and a fixed-probability binomial reference (κ=null). Generate 2,000 replicates per profile/sample-size/arm: 160,000 rows total. For finite κ draw p~Beta(μκ,(1−μ)κ), then x~Binomial(n,p); for null concentration use x~Binomial(n,μ). Fresh seed base 88100000, row key `88100000 + profile_index*20000000 + n*100000 + arm_index*10000 + replicate`, pair seed `key*10+pair_index`; CPython 3.12.10 `random.Random.betavariate`/`binomialvariate`. A10 seeds do not overlap A06/A07/A08/A09. Candidate sees opaque arm IDs, IDs/n/counts but not concentration or truth.

**D.** Method PASS only if all 160,000 rows and candidate outputs reconstruct exactly with zero base errors and all five frozen mutations rejected. Independently report for each arm which unchanged gates have Wilson 95% lower bound ≥.80 for every positive and upper bound ≤.05 for every null, across both n values. No arm/gate post-result expansion or selection outside this finite table.

**C.** Discrete authored concentration grid; fixed reference arm; independent per-pair/per-replicate latent draws; profile taxonomy, seed sets, sample sizes, Wilson bounds and numerical thresholds are synthetic assumptions. Concentration is not estimated from participants.

**U.** Method/frontier sensitivity evidence only; no actual learner or GUI calibration, concentration estimate, sample-size recommendation, T1, human learning, runtime, or safety claim. Does not revise prior allocation records.

## Execution

- #8084 remains open. A10 is a distinct fresh allocation; no A06–A09 outputs are reused.
- Base main full SHA recorded in FREEZE.json; branch `research/8084-overdispersion-frontier-a10-20261005`; unique package path `research/analysis/confusion_adaptive_practice_8084_t0_a10_20261005/`.
- Windows x64; exact CPython 3.12.10 path `C:\Users\junny\AppData\Local\Programs\Python\Python312\python.exe`.
- Before formal calls: `git add --sparse`, require zero exit; freeze commit, require zero exit; verify freeze blob in HEAD and package clean. Any precondition failure aborts all formal calls.
- Invoke generator, candidate, auditor exactly once each; preserve outputs/status; do not retry.
- Host-only standard-library processes. No WSLc/Docker (management gate remains untouched), network, GPU, GUI, model, participant, external data or shared service. No container-isolation/resource enforcement claim.
