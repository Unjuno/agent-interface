# MAP01 measurement integration live v3

Status: **FROZEN PROTOCOL REPAIR — NOT YET EXECUTED.**

Allocation: `map01-measurement-integration-live-03`  
Immutable base: `5486ea20b417a80903619a384744cf9ac38d5a52`

## Why a v3 allocation is required

The live-02 mechanism passed in both retained executions, including direct release measurement and posthoc five-field terminal scorer agreement. The formal allocation nevertheless failed because the one-shot workflow executed twice. Selecting one favorable result would violate the preregistration.

V3 changes only experimental protocol. The MAP01 probe, v13/v12 session mechanics, release telemetry v3, scorer adapter, progress clock and direct retained-input analyzer remain byte-identical to the hashes frozen in the preregistration.

Two protocol changes are added before/after the unchanged formal probe:

1. GitHub Actions uses a non-cancelling concurrency group, requires `GITHUB_RUN_ATTEMPT == 1`, and invokes the retained earliest-run ownership guard before the formal probe. A later matching run must stop before consuming the allocation.
2. The retained terminal-score agreement audit is mandatory after the probe; the final independent scorer sample must strictly equal `score.json` on map exit, episode terminal, player dead, death count and kill count.

## H / T / D / C / U

**H.** A separately versioned one-shot allocation can reproduce the measurement-integration mechanics while enforcing exactly one formal probe execution and strict terminal scorer agreement.

**T.** Revalidate the frozen mechanism hashes, 10-case launch-owner guard, integration regressions, terminal-score audit and preregistration. Then allow one canonical workflow run to execute the unchanged 250 ms `a+d` hold probe at seed 990614. No model call or policy experiment is permitted.

**D.** PASS requires canonical launch ownership, exactly one formal probe execution, the existing measurement-integration audit, direct retained-input readiness, zero scorer leakage/missed periods, verified empty releases, and terminal-score agreement. A duplicate contender rejected before the formal step does not consume another scientific allocation; it remains launcher evidence. Any second formal probe execution invalidates v3.

**C.** GitHub Actions API visibility could still race; dependency installation could fail; ViZDoom/X11 behavior could differ; scorer terminal state could disagree despite the earlier posthoc 2/2 result. Any such first result is retained without retry.

**U.** This is still a measurement gate, not recovery efficacy. Even a PASS does not prove recovery cover helps survival/progress or human tempo.

## Next gate

If v3 passes, the measurement prerequisite for the already-frozen recovery-vs-coast question is satisfied. A separate explicit live-experiment lease and single-run-protected launcher are still required before consuming that efficacy allocation.
