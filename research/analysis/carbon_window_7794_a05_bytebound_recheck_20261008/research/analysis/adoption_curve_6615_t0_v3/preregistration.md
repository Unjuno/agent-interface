# Preregistration — Issue #6615 adoption-inclusive verified-work curve

Allocation `ADOPTION-INCLUSIVE-CURVE-6615-T0C-20261002-01` (successor to failed T0 and T0B; predecessor evidence unchanged)  
Frozen main base `afea9a530cafd7af529df4c9e59f36b816bca24f`  
Additive path `research/analysis/adoption_curve_6615_t0_v3/`  
Scope: deterministic synthetic accounting-method test only; no human, GUI, model, telemetry, onboarding, adoption, or product claim.

## H / T / D / C / U

**H.** Prepared-only speed can rank a route differently from first-use cumulative cost when setup/repair overhead, failures, learning and route eligibility are counted; an accounting gate will expose a crossing only where both routes delivered the same exact verified task prefix. It will never impute successful work from an attempted/unsupported task.

**T.** Freeze nine finite host/cohort scenarios in `fixture.json`: zero setup delta, setup-dominates-horizon, task-level learning with a late break-even, failed setup, app-change repair, route-ineligible task, wrong/unverified effect, unsupported host, and no-follow-up control. Emit one event-sourced ledger for direct and guarded routes, including setup, every assigned task, repair, failure and cumulative wall/active time. Compare first-use cumulative cost only at prefixes where both routes independently verify every same task ID; otherwise mark quality incomparable and report failures separately. Independent raw-only auditor reconstructs each event/cumulative total and crossing.

**D.** `PASS_METHOD_SCOPED` iff construction tests pass; the frozen positive crossing is found at prefix 5, setup-dominates yields no crossing through K=5, zero-delta ties at prefix 0, unsupported-host has no comparable prefix, and all five mutations (drop setup failure, attempted-as-success, unsupported-as-success, drop setup cost, free repair) are rejected. Comparable prefixes additionally require both route rows to explicitly indicate supported hosts, preventing vacuous zero-task prefix comparisons. Any unsupported route or unequal verified task prefix is never credited as a quality-preserving speed crossing. Setup-failure counts exclude unsupported-host setup rows, which are separately stratified; ineligible-task counts include only tasks actually attempted on a supported, successfully set-up route.

**C.** T0 stipulates costs and task outcomes; actual support burden can be negligible or reuse can amortize faster. A repaired app may remain unavailable, and any T1 must independently determine supportable hosts and preserve full failure denominators.

**U.** No real operator effort, credentials, app installs, model cost, task mix or usage horizon is measured. The synthetic crossing cannot infer adoption, preference, population benefit, or product economics. The exact preparation-time ledgers retained by PR #6628 are an adjacent empirical input, not reused or treated as first-use setup evidence here.

Predecessor T0 (path `adoption_curve_6615_t0_v1`) failed because it treated the unsupported-host empty prefix as comparable. T0B (path `adoption_curve_6615_t0_v2`) fixed that gate and its result passed structural/method checks, but candidate stdout still emitted T0's stale allocation ID. Both frozen evidence sets and failure records remain unchanged. T0C tests and formally checks the stdout allocation identity against fixture and preregistration before interpreting the audit.

## Environment and freeze gates

One host-local CPython standard-library run is permitted only if WSLc is unavailable and no container-specific behavior is needed; report it as host-only. Here `wslc.exe` is not installed on macOS and the OrbStack Docker daemon is nonresponsive to a read-only probe; do not start or alter shared containers. One candidate invocation and one separate auditor invocation, zero retries. Freeze source/fixture/test hashes and verify outputs absent before execution. Preserve raw output and all exits/hashes before GitHub publication.
