# WSLc lifecycle-amortization replication (successor to Issue #5084)

## H — hypothesis

For the exact retained seed-3788 three-role numeric skill package, a `LOAD_ONCE_REUSE` arm that fully parses/validates the artifact and constructs all roles once will produce the same outputs as `RELOAD_EACH_REQUEST`, while costing less lifetime CPU time over the frozen 1,000-request A/B/C schedule in the native WSLc runtime. This is a WSLc-specific scoped replication, not a cross-runtime speed ranking.

## T — treatment and freeze

One fresh allocation: `NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-5084-T0-20261002-01`; branch `research/needle-role-skill-lifecycle-wslc-5084-20261002`; path `research/analysis/needle_role_skill_lifecycle_wslc_5084_t0_20261002/`. Base main is recorded in `FREEZE.json`. Inputs are the exact merged seed-3788 `skill.json` and `expected.json`, verified against the immutable hashes from #5053/#5084. Corrected scorer and validator are the exact current-main files named and hash-pinned in the freeze.

Run 15 paired AB/BA blocks, each arm receiving the same 1,000 requests; request `i` selects role A/B/C by `i mod 3` and fixture row `(37*i+11) mod 4096`. Reload arm loads, validates, and builds only the selected role for each request. Reuse arm includes full validation and all-role build once in `initialization_ns`, then reuses those models. Process startup is excluded equally; reuse initialization is included. Candidate is one invocation; the independent standard-library raw auditor is one invocation only after candidate exit 0. Construction tests are separate and precede the candidate.

Runtime: Microsoft WSL Containers (`wslc`), WSL 3.0.1.0; cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64, CPython 3.12.14. No image pull, network, GPU, model, training, GUI, or user data. Candidate and auditor use separate `--rm` containers; `--pull never --network none --cpus 0.25 --memory 512m --user 65534:65534`. Source, reference code, and input mounts are read-only; only a newly-created output directory is writable. Root filesystem remains writable because WSLc exposes no rootfs-read-only flag; memory/swap enforcement is not assumed. Capture WSL/cgroup warnings and container cleanup status. Stop if another allocation is using shared CPU/memory or the host preflight detects a conflict.

## D — decision

`PASS_LIFECYCLE_AMORTIZATION_WSLC_SCOPED` requires: construction parity 12,288/12,288; all 30,000 formal predictions equal retained expected labels and an independently implemented raw-tensor oracle; unchanged source/reference/input/image identities; all 15 blocks complete with positive timings; reuse total lifetime cost wins at least 12/15 blocks; median `(reuse initialization + reuse request time) / reload request time` <=0.90; median paired first break-even request <=1,000 (non-crossing blocks are censored as 1,001); and seven independent corruption controls are rejected. Integrity/provenance errors are STOP; quality/parity mismatches are FAIL; unmet amortization gates are HOLD. No retries, replacements, tuning, or pooling with #5084/#5053 allocations.

## C — controls and confounders

Paired arms use identical immutable bytes, request order, scorer, Python image/runtime, process boundary, and alternating order; only lifecycle differs. Scheduler noise, cache state, Python-version/runtime effects, and the single fixed synthetic package limit inference. Previous #5084 proposals used an OrbStack CPython 3.13.5 image and STOPped before formal execution; this run must not be compared numerically with that unexecuted plan or claimed as an environment speedup.

## U — scope

One retained synthetic package/seed on one host and one WSLc/Python image. No PyTorch/framework speed, production workload, general lifecycle benefit, learned-skill efficacy, GUI/task success, product latency, GPU, or cross-runtime claim.
