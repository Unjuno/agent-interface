# Issue #6678 T0 — Blackwell observation-channel dominance

**Disposition: `METHOD_PASS_SCOPED`.** The exact LP candidate and a separate read-only-input auditor completed once each in separate OrbStack containers; both exited 0. This establishes only the frozen finite synthetic method result below. Issue #6678 remains open for empirical channel estimation and any real Agent Interface claim.

## H / T / D / C / U

- **H:** On a three-state common sample space, exact garbling feasibility will identify the fully informative `fine` channel above each state partition, the partitions above `uninformative`, and `partition_s0` / `partition_s2` as incomparable. Independent Bayes-risk enumeration will give opposite task-conditioned preferences for those two partitions.
- **T:** Frozen exact-rational kernels, uniform prior, four channels, four decision/loss tables, zero tolerance, one state/action/output relabeling, and three corruption/leakage controls. The candidate enumerated basic feasible supports for all 16 ordered channel-pair LPs. The independent auditor checked positive stochastic-matrix certificates and enumerated every deterministic output-to-action rule for all four loss tables. Construction max 1, candidate max 1, auditor max 1, retries 0.
- **D:** **Pass.** All 16 LP verdicts matched the preregistered relation matrix; every positive relation carried a valid exact rational garbling matrix; every negative relation had an independent strict Bayes-risk counterexample. The two partitions had opposing decision-specific risk rankings; relabeling preserved risk; certificate, observation-label/channel-identity, and fixture-kernel mutations were rejected. Audit errors: 0.
- **C:** Finite, authored, exact-rational synthetic kernels; no stochastic sampling, so no seed was used. OrbStack Docker Engine 29.4.0, linux/arm64; image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`. Three distinct containers used `--network none`, read-only rootfs, `--cap-drop ALL`, no-new-privileges, UID/GID 65534, and requested 0.25 CPU / 256 MiB / 32 PIDs. Docker inspect records these requested settings. The daemon reports 10 CPUs and 16,819,609,600 bytes; effective per-container cgroup enforcement was not independently observed, so no enforcement claim is made.
- **U:** No real screenshot/tree/event channel was sampled; no channel-kernel estimation, LLM decision behavior, action authority, GUI effect, latency/tokens/attention, user benefit, safety, transfer, or product claim follows. This applies only to a common finite state set, exact stable kernels, the uniform prior, and these four loss tables.

## Formal container results

| Stage | Container ID | Exit | Result |
|---|---|---:|---|
| Construction suite | `b41a3322792523e1a33f0a46a47c51bc8c98d3dfd08d9bd4e9761a338f1fc6e2` | 0 | 5/5 tests pass |
| Candidate LP enumeration | `d876d3e2c08c177e87bcbf91cb766811bbde4a8887f048cd546ffe389d88f276` | 0 | 16 ordered channel pairs classified; exact rational certificates emitted |
| Separate raw-only audit | `93cc55fab0ae56a39897b075ba1cde3d0d90810e350357e4f86c1bdcf2a1370c` | 0 | `METHOD_PASS_SCOPED`; 0 errors |

Risk values are exact expected losses under the uniform prior (lower is better):

| Decision problem | `fine` | `partition_s0` | `partition_s2` | `uninformative` |
|---|---:|---:|---:|---:|
| exact target | 0 | 2/3 | 2/3 | 1 |
| focus on s0 | 2/3 | 2/3 | 1 | 1 |
| focus on s2 | 2/3 | 1 | 2/3 | 1 |
| s0 deadline/lateness loss | 2 | 2 | 3 | 3 |

Both partitions have the same marginal output probabilities `{1/3, 2/3}` and the same two-output entropy, yet `focus_s0` prefers `partition_s0` while `focus_s2` prefers `partition_s2`. Thus, within this finite fixture, marginal entropy alone does not induce a universal decision ranking. This does not rank real observation modalities.

The candidate raw SHA-256 is `74036b811e1dd91e35742d7cc3632bbe9050fd8c22c41970822b340bb9888180`; the independent audit JSON SHA-256 is `80e43e5167ee14d54cb7d973773c0593db752ef748b1ad3c1283fab928d572f2`. The auditor consumed the candidate JSON mounted read-only at `/in`; it imported no candidate code. Full stdout, exit markers, inspect records, raw JSON, protocol, and digests are retained in this directory and enumerated by [`SHA256SUMS`](SHA256SUMS).

The experimental branch was prepared from main `f0242a7476d7ac12dedcf932ebfd18b82d583fca`. Before any formal process, concurrently merged main through `5f1cc2624469dea4624e98062423e928da083ca4`, confirmed no overlapping Blackwell research paths, regenerated the analysis index, and updated the freeze. Candidate, fixture, auditor, construction tests, runner and image ID match the committed freeze hashes. No formal invocation was retried.
