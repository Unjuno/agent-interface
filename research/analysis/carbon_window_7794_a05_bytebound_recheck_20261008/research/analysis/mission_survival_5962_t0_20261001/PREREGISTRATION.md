# Issue #5962 — mission survival T0 (allocation 01)

## H / T / D / C / U

- **H:** Per-task success marginals alone do not identify persistent-session survival or burst-risk ordering. For three stationary binary Markov outcome models with identical `P(success at task t)=4/5`, dependence should change mission survival in endpoint-specific and potentially opposite directions.
- **T:** Exact-enumerate every binary path of length N=1..8 under three frozen kernels (IID, clustered failures, alternating failures), all initialized at the common stationary distribution. Retain full path probabilities. Score (i) terminal failure on any F and (ii) terminal failure on an FF run. Separately compute operational observed-prefix length, censored suffix length, denominator inclusion, and complete potential-path maximum F-run. A raw candidate emits rows; an independently implemented auditor recalculates probabilities and endpoints, verifies every marginal and total mass, and challenges five corruptions.
- **D:** `PASS_METHOD_SCOPED` only if each kernel has exact stationary failure marginal 1/5 at every task; each path's rational probability is independently reconstructed; all 3×(2^N) path sets sum to one for each N; candidate endpoint/censoring fields reconcile; model rankings differ for both endpoint families by N=8; the all-started-session denominator is preserved; and all five corruption controls are rejected. Otherwise retain HOLD/FAIL with no post-freeze rerun.
- **C:** The three kernels are synthetic and chosen, not measured route dynamics. Equal binary margins do not model task heterogeneity, state carryover, restoration, safety effects, adaptive tasks, or empirical uncertainty.
- **U:** Exact finite probability model only. No repository benchmark route, agent, application, user session, production reliability, or causal interface benefit is estimated.

## Frozen model and semantics

Task result `S` means independently verified success in this stylized model; `F` means the one typed mission-ending failure. A complete potential-outcome sequence is sampled from a stationary first-order Markov chain. An operational trace observes only through its endpoint: first F for endpoint `any_failure`, or the second F of the first adjacent FF pair for endpoint `failure_burst_2`. All initiated sessions remain in every denominator; later potential outcomes are censored, not removed. Maximum F-run is summarized over the complete generated potential path and explicitly is not claimed as post-terminal observable data.

All kernels have stationary `P(F)=1/5`:

| kernel | P(F|S) | P(F|F) |
|---|---:|---:|
| iid | 1/5 | 1/5 |
| clustered | 1/20 | 4/5 |
| alternating | 1/4 | 0 |

Lengths 1..8 and all 256 maximum binary paths are enumerated exactly with rational arithmetic; no random sampling or fitted parameter is used.

## Execution boundary

Source base: current main `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc`. Host is Windows CPython standard library, CPU-only. Docker Desktop's `desktop-linux` context exists, but read-only `docker info` remained unresponsive and was interrupted; no container/shared allocation was started. No GPU, model, GUI, network, user data, or external input. Construction tests run before freeze. After freeze, the candidate is invoked once and the separate auditor once. No retry or source edit after candidate execution.
