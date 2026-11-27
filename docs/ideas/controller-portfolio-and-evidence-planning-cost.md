# Controller portfolio size and evidence-planning cost

These open Issues ask two separate questions about computation spent deciding how to act. #8864 treats the number of available, already-qualified controller routes as an architecture factor. #8851 treats the cost of evaluating many already-permitted evidence actions. Neither permits a proxy score to weaken correctness, authority, freshness, effect, or release gates.

## #8864: workload-dependent controller portfolio size

- **Status:** open, unverified proposal; no comments, result, implementation, or evidence PR was found in the current Issue/PR read.
- **Idea:** Compare nested portfolios of qualified routes across fixed task/context strata with varying heterogeneity and selector/coordination/qualification costs. Charge selection, failed escalation, compute and validation cost; compare against the best single route, a fixed full portfolio and an oracle upper bound. The hypothesis is an interior portfolio size whose net value changes with workload heterogeneity and selection cost, not that more tiers are better.
- **Decision boundary:** Correctness, authority, freshness, effect and release gates remain identical and non-compensable. A synthetic result cannot authorize adding/removing production mechanisms or establish live GUI benefit.

## #8851: topology-guided evidence-action shortlist

- **Status:** open, unverified proposal; no comments, result, implementation, or evidence PR was found in the current Issue/PR read.
- **Idea:** For an already-permitted finite set of non-effecting evidence actions, use a topological signature only to order or shortlist candidates, then apply exact decision-value evaluation to retained candidates. If the bound cannot exclude a better omitted action, or the graph is outside its qualified class, fall back to full exact evaluation or return UNKNOWN.
- **Adversarial boundary:** Keep topology-preserving changes to factor strength, noise, correlation and task loss, plus small candidate sets where exact computation is cheaper. The test must count total computation and regret, not only exact-evaluation calls. A topology score never grants action authority or replaces provenance, freshness or safety checks.

## Keep the estimands separate

#8864 changes portfolio cardinality and measures useful effects under a fixed offered task stream. #8851 keeps the admissible evidence-action set fixed and asks whether a structural proxy can reduce inference work without losing the exact-value-best option. The first is an architecture-selection question; the second is a bounded search-cost optimization. Both remain proposals; neither has an allocation or result recorded here.
