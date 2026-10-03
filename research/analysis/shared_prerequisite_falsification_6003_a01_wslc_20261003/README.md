# Issue #6003 A01 — shared-prerequisite falsification leverage

Status: PASS_METHOD_SCOPED. Candidate and independent auditor each completed once in WSLc, exit 0; 72 outcome rows were reconstructed and all eight effective corruptions rejected. See [REPORT.md](REPORT.md), [RUN.json](RUN.json), and [the retained raw results](results/). This is a finite synthetic method test, not a research-productivity result or an assurance proof.

## H / T / D / C / U

- **H:** In a frozen claim portfolio with two top decisions sharing one necessary premise, a graph-aware next-experiment card will select the test whose possible independently adjudicated outcomes change the eligibility set of more top decisions than a raw node-degree selector, cheapest-first, or the prior-robust decision-reversal selector. It will not award leverage to a high-degree but irrelevant node, an unvalidated relation, duplicated same-origin support, `HOLD`/`STOP`, or an incomplete graph.
- **T:** Exhaustively enumerate the finite AND/OR/defeater fixture in `fixture.json`, subject to a fixed cost budget with a mandatory safety sentinel. Compare cheapest-first, raw declared out-degree, the bounded #6003 robust decision-reversal baseline, and the graph-aware maximum number of top-claim eligibility changes. Controls include a disjoint portfolio, null portfolio, unknown graph coverage, one false edge, one correlated duplicate source, redundant independent support, and `HOLD`/`STOP`. Run one candidate and one separately implemented raw-only auditor in distinct network-disabled WSLc containers; no GUI, model, GPU, host input, or external service.
- **D:** `PASS_METHOD_SCOPED` only if the independent oracle reconstructs every selector and every before/after decision set; graph-aware chooses `E-shared-prerequisite`; cheapest-first chooses `E-cheapest-inert`; raw degree chooses `E-degree-decoy`; legacy robust reversal chooses `E-verify-unique`; the disjoint graph changes at most one top claim and chooses `E-verify-unique`; null and incomplete-coverage controls are `UNRANKABLE`; the mandatory sentinel remains in budget; invalid/correlated evidence is not inflated; and all eight auditor corruption controls are rejected. Any mismatch is retained as FAIL/HOLD without candidate retry.
- **C:** The ordinary #6003 decision-reversal card may already capture the practical decision value; graph construction may add overhead and false certainty. A direct static checklist could be simpler. If all eligible tests have the same downstream decision set, the graph-aware selector must abstain.
- **U:** The portfolio, claim rules, source IDs, and outcome tables are authored synthetic data. Claim coverage and edge validation are stipulated inputs, not externally proven facts. The metric counts changed eligible top claims rather than calibrated utility; it does not establish real-world decision value, productivity, safety, or empirical priors.

## Provenance and non-duplication

This allocation implements the distinct prospective shared-prerequisite comparator in [#6003 comment 5944231272](https://github.com/Unjuno/agent-interface/issues/6003#issuecomment-5944231272). It does not rerun the host-only #6003 T0 or the #6744 container-reproduction A01/A02, and it does not implement #5332's assurance-case evaluator or provenance-polynomial comparator. Historical results remain unchanged.

The exact main SHA, source/fixture hashes, image digest, commands, and gates are in `FREEZE.json`. Candidate output and independent audit are kept in `results/`; the WSLc invocation receipt and SHA-256 manifest are additive records.

## Scope boundary

The WSLc memory value is only a requested limit; host cgroup/swap warnings are retained and no effective memory cap, OOM protection, runtime speed, Docker parity, native-WSL benefit, or general migration benefit is claimed. The package changes no runtime/default/workflow behavior.
