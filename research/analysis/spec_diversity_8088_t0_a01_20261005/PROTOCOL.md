# Issue #8088 T0 A01 — specification-diverse challenge method study

Allocation: SPEC-DIVERSITY-8088-T0-A01-20261005-01. Current-main base: 1fbef34f244588bff3d79b7cbea423dcb510ef8f. Additive package: research/analysis/spec_diversity_8088_t0_a01_20261005/. The only contract input is CONTRACTS.json; no production code, user data, GUI, model, participants, or consequential action.

## H / T / D / C / U

- **H:** For the frozen eight explicit task contracts, a blinded second decomposition plus contract-only adjudication identifies at least one otherwise-surviving omission mutant that violates an explicit contract clause but is absent from the primary decomposition; the challenge invents no requirement and classifies ambiguity as UNKNOWN/HOLD.
- **T:** Freeze contract text, initial states, scope boundaries, task IDs, and this protocol before authoring. Primary and challenge authors receive only the frozen contracts and this protocol, in isolated contexts, before seeing each other's outputs or any candidate/auditor code. The primary decomposition alone feeds the candidate/scorer and an independently authored raw-only auditor. Freeze those artifacts and ordinary implementation mutations before revealing the challenge decomposition. A third isolated reviewer sees contracts and both decompositions but not candidate outputs/mutation outcomes; each divergence is labeled contract-anchored omission, harmless wording/partition, or unresolved ambiguity with quoted clause. Predeclared generation rule: for every adjudicated omission in one of four classes (destination, persistence, forbidden side effect, UNKNOWN handling), create exactly one mutation violating only that clause. Evaluate whether ordinary primary-spec controls accept it and the specification challenge rejects it. Independently recompute all classifications. Distinct agent contexts use the same configured assistant service; this does not establish human or model-family independence.
- **D:** METHOD_PASS_SCOPED iff all author/reviewer role-isolation receipts are complete, every injected mutant is linked to an explicit contract clause, at least one such mutant is accepted by the ordinary primary-spec oracle but rejected by the contract challenge, no false requirement is accepted, unresolved differences remain UNKNOWN/HOLD, and independent raw audit matches all rows. NO_INCREMENTAL_VALUE_SCOPED iff the same gates pass but no qualifying surviving omission is found. HOLD if blinding/role isolation fails, no defensible adjudication exists, or no independent audit is available. FAIL for any invented requirement, ambiguity promoted to fact, missed predeclared fault, or oracle/audit disagreement.
- **C:** Existing raw-only checks and implementation mutants may already detect every relevant omission; a contract challenge may add cost without incremental fault detection. Different decompositions may only repartition fields. An authored mutation suite cannot estimate real-world common-mode error rates.
- **U:** Eight self-authored synthetic contracts and AI-agent authorship only. No estimate of production audit failure, cognitive independence, human interpretation, real app behavior, usability, or correctness of existing repository results.

## Method and one-shot boundary

Two contract authors are separate isolated agent contexts. The primary role is fixed to the delegated author; the main agent is the challenge author. Before seeing either decomposition, the exact protocol, contract bytes, author prompts, and roles are frozen. Primary/scorer and challenger are independently hash-bound. A distinct raw-only auditor derives from the primary decomposition and is frozen before formal execution. The adjudicator cannot see any output or mutant result.

Formal candidate and auditor each run exactly once after final freeze, with zero retries. Construction tests may run before final freeze. The candidate creates baseline and mutation-case state transitions deterministically from the frozen contracts and frozen decompositions. The auditor independently reconstructs contract clauses, state transitions, mutation outcomes, and scoring without importing candidate code. Missing/nondeterministic fields or unbound source hashes are STOP, not scientific outcomes.

## Runtime

OrbStack Docker API is reachable (29.4.0 linux/aarch64) but `docker image inspect python:3.12-slim` fails with containerd blob `operation not supported`. No shared-daemon repair, prune, or restart. As this issue's T0 is explicitly a standard-library method study with no special runtime requirement, the frozen fallback is native macOS standard-library CPU-only execution; no isolation/resource-enforcement claim.

## Interpretation boundary

Even METHOD_PASS_SCOPED only establishes detection of a bounded authored omission mutation in this synthetic method packet. It does not prove independent authorship in the human/cognitive sense or invalidate any prior repository result. Human reviewers may later choose to evaluate the packet, but are not modeled as user intent or as a gold-standard majority.

