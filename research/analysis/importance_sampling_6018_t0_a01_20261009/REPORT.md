# #6018 A01 — likelihood-ratio correction of adversarial fault-search samples

**Disposition: PASS_METHOD_SCOPED** (independently audited synthetic finite-method result; **not** live GUI or runtime safety). The experiment was prospectively frozen in [the owning Issue](https://github.com/Unjuno/agent-interface/issues/6018#issuecomment-6070911843), before one formal candidate and one independent auditor invocation. Main intake commit: `57337e95ecbecf7e762c8ec8091472b79e8ad49f`. Earlier #5380 results are untouched.

## H/T/D/C/U

**H:** Under a declared IID four-fault model, useful biased sampling Q will find the exact planted unsafe event at least 4× earlier in median samples than sampling from reference P, detect in ≥12/16 batches, make unweighted Q event frequency ≥10× the true P rate, and deliver a likelihood-ratio-corrected rate within 15% relative of P. A highly concentrated Q must retain high-variance uncertainty, and any loss of proposal support, independent evaluation or operational reference P must return HOLD.

**T:** Freeze 4 independent Bernoulli faults and the exact event; enumerate all 16 masks. Four valid proposal arms (direct P, useful Q, uniform Q, concentrated Q), 16 distinct batches × 4096 masks each, 262,144 total sampled masks. Predeclared seed for arm index `a`, batch `r`: `20261009 + 97*r + 1000003*a`. The independent auditor reruns each seed, recomputes every mask count, sample-stream hash, first failure and preserved counterexamples, likelihood ratios and 16-path oracle, and injects seven effective mutations. Construction used distinct small seeds and never contributes to the formal sample.

**D:** PASS only if all 7 mutations are rejected, 64/64 batches reconstructed, all H bounds met, concentrated Q is flagged for high theoretical variance, and missing-support / same-stream adaptive proposal / absent real reference P are all labeled `HOLD_UNIDENTIFIED` without a point estimate. Otherwise FAIL/HOLD without retuning A01.

**C:** Full 16-path enumeration needs no Monte Carlo; Q-uniform may dominate Q-useful at the expense of more injected faults, and a pathological oversampler may have intolerable weight variance. A probability model lacking observational justification cannot be used to infer a deployed rate.

**U:** The IID fault distribution and event predicate are authored; no real host/model failure distribution, correlated scheduler, deadlines, GUI effects, physical input release, confidence coverage in deployment, human tempo, or operational risk is tested. The result qualifies only this finite synthetic method.

## Variables, dimensions and proof

| Symbol | Meaning (日本語) | SI unit | Definition / domain | Type |
|---|---|---|---|---|
| `S,D,V,C` | 故障フラグ4種（旧観測・ACK重複・検証遅延・共通原因） | 1 | independent Bernoulli in `{0,1}` | Boolean scalars |
| `m` | 4ビット故障状態 | 1 | integer 0..15 | integer scalar |
| `H(m)` | 危険な権限承認の合成述語 | 1 | `D and ((S and (V or C)) or (V and C))` | Boolean scalar |
| `P_m,Q_m` | P基準分布とQ提案分布の状態質量 | 1 | each in [0,1], sums to 1; for estimation Q_m>0 wherever P_m>0 | rational probabilities |
| `w_m` | 尤度比 | 1 | P_m/Q_m, finite only under support | rational scalar |
| `p` | P下の合成故障確率 | 1 | sum over 16 masks of P_m H(m) | rational probability |
| `n,R` | 1バッチ試行数・バッチ数 | 1 | 4096,16; positive integers | integer scalars |
| `X_i` | Qから生成した故障状態 | 1 | 0..15 | discrete random variable |
| `p_hat` | 尤度補正故障確率推定 | 1 | average of `w_X H(X)` over nR draws | rational random scalar |
| `u_c,k` | 推定値の合成標準不確かさ、係数 | 1 | `u_c = sqrt(Var_Q(wH)/(nR))`; `k=2` is descriptive only | nonnegative scalars |

P is `[1/32,1/16,1/24,1/16]`. Under independence and inclusion–exclusion, conditional on D the event is `s(v+c-2vc)+vc` with `s=1/32,v=1/24,c=1/16`. Since `v+c-2vc=19/192`, that quantity is `19/6144+16/6144=35/6144`. Multiplying `P(D)=1/16` yields **p = 35/98304 = 0.0003560384114583333**. An independently enumerated 16-mask oracle agrees.

With full Q support, the expected importance-weighted event is exactly the reference rate because `sum_m Q_m(P_m/Q_m)H(m) = sum_m P_m H(m) = p`. Conversely, the unweighted count estimates `sum_m Q_m H(m)`, not p. Variance under the model is `sum_{H(m)=1} P_m²/Q_m - p²`, divided by `nR` for `u_c²`. All factors are probabilities, hence these expressions and `u_c` have SI unit 1; this is the requested dimensional check. No independence or support means no such risk claim.

## Retained one-shot outcomes

| Arm | Median first violation (sample index) | Found / 16 | Observed raw Q event fraction | Corrected P estimate | P-relative error |
|---|---:|---:|---:|---:|---:|
| Direct P | 1928.5 | 12 | 0.0003356934 | 0.0003356934 | -5.71% |
| Useful Q | 18 | 16 | 0.03895569 | 0.0003551046 | -0.26% |
| Uniform Q | 3 | 16 | 0.2511597 | 0.0003581022 | +0.58% |
| Concentrated Q | 1 | 16 | 0.9100189 | 0.0003271714 | -8.11% |

Useful Q finds the synthetic violation 107.1× earlier by median **sample index**, not wall-clock; raw event fraction overstates P by ~109×. Uniform Q is faster here but injects an average of 2.005 faults/sample versus useful Q's 1.004. Q-useful's conditional analytical `u_c=0.0000074791` for all 16 batches, with descriptive `k=2` spread ±0.0000149582; no validated 95% deployment coverage is inferred. Concentrated Q has theoretical relative standard error per batch 1.145 (>0.25), so apparent point-estimate closeness cannot certify precision. The three unsupported controls remain `HOLD_UNIDENTIFIED` without P estimates.

Candidate and auditor each exited 0, no retries. Independent raw audit reconstructed **262,144/262,144** samples and 64/64 batch traces, rejected 7/7 mutations and returned `PASS_METHOD_SCOPED`. Source SHA256: spec `35c54e5877a6e73bc09a4db5811c3fcb69ef15a470cad03951448d546cb305df`, candidate `aa5ea9c868f658713b5908ce2d0c4db53cde2a1639b5bf0dbc0c06ab12623792`, auditor `30e08f7f3cb2b6fcae187ed9c9382b66cd8f2c7e8c1673ea0de7b5c2d72bdd9a`. Raw candidate `a0dd810be29acb27c96c5167076d059f71b22ed4da45386c028ae0f372040706` (49721 B), auditor `f6076dd19c725745f7ff86d7095c8cee11b46a59c5d84f7f9d34d4c1fb2c84f2` (1363 B), first-run receipt `dbbe2647e808028f4f4ffb820b75f60e55d882b3fb264d5a4f2c43d4e84455fa`.

**Environment:** tool-provided Debian 13/Linux x86_64; CPython 3.13.5 standard library, glibc 2.41, reported cgroup CPU quota 400000/100000 and 4 GiB memory maximum (enforcement not independently proven). One observed process candidate 2.508 seconds, auditor 7.050 seconds; no repeated timing, HW core-clock pinning, or performance benchmark claim. No image digest available, and this is not macOS/WSLc/OrbStack qualification. Full stdout/stderr, UTC process times, source, spec, construction-only records, hashes, raw and auditor are preserved in the archive: SHA256 `6d65b164436dece48158ed9575cc339de072ee51f52f97c932fb2d8253c42798`.

## ERROR CHECK and next transfer gate

Exact reference enumeration, source freeze, sample replay, likelihood reconstruction, rejection of 7 corruptions, absence of P estimates in three invalid scenarios: **PASS for the authored fixture**. A model that correctly importance-weights samples cannot repair a false P distribution or a missing effect oracle. Before integrating with #59, identify and independently calibrate real disturbance distributions and effect/release outcomes under a separate authorized live allocation; retain deterministic authority checks. Relevant disciplines: statistical model checking, importance sampling, software assurance, and real-time control.
