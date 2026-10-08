# Issue #5916 T0 construction plan

Status: construction only; no formal allocation consumed yet.

## H / T / D / C / U

- **H:** For deterministic typed explanations, dependency-closed perturbation checks can expose uncited or stale decisive evidence while accepting alternative sufficient proofs. The counter-hypothesis is that a machine-produced exact decision trace provides the same defect coverage at lower complexity, so a new audit layer adds no value.
- **T:** Ten immutable synthetic bundles, two frozen policies, four methods (provenance presence, naive per-citation deletion, exact machine trace, dependency-closed explanation audit), and a separately implemented truth-table auditor. No model, GUI, Docker service, external authority or input effects.
- **D:** Method-scoped pass requires every planted defective explanation flagged; all valid alternatives/context cases accepted; invalid deletion explicitly `UNTESTABLE`; exact trace compared on defects and coverage; truth-table auditor reproduces every policy outcome and control. Any missed defect or false flag fails; invalid/circular bundle holds. Report separately whether perturbation adds any defect-detection coverage over the exact trace. If not, the experiment may pass the test method but the added audit layer is `NOT JUSTIFIED` for this fixture.
- **C:** Synthetic predicates simplify proof structure; this cannot establish human comprehension or live receipt completeness. Exact traces may dominate the extra audit.
- **U:** One tiny Boolean policy family; no model-faithfulness, production, user-comprehension, or live causal claim.

## Frozen fixture cases

Necessary ALLOW; two alternative DENY predicates; redundant independent proof DAGs; context-only citation; decisive uncited blocker; stale epoch; legal contradictory replacement; illegal mandatory deletion; p1-to-p2 policy swap with unchanged rationale text. Invalid deletion is not evaluated as a causal counterfactual. The redundant-proof case uses a dedicated frozen `proof_union` rule so two independent certificates are genuinely each sufficient; the separate p1/p2 cases retain the allow/deny policy family.

## Formal protocol

1. Record the source freeze commit and SHA-256 for fixture, candidate, auditor, and tests.
2. Read all files back from the frozen source commit.
3. Run the candidate once and retain exact JSONL/stdout; run the independent auditor once.
4. Preserve a failed or stopped formal outcome as-is; no retry/relabel.
5. Record hashes and scope in REPORT/RUN/TESTS/SHA256SUMS.

Docker Desktop is installed but its daemon was observed stopped; no shared compute lease was visible for this Issue. This fixture has no external effects and is CPU-only, so use host CPU to avoid starting or consuming shared Docker resources without a lease. This is a deliberate method exception, not a Docker result.

Candidate results will be compared against exact-trace baseline, not just the weaker provenance/deletion controls. No authority is granted by synthetic counterfactuals.
