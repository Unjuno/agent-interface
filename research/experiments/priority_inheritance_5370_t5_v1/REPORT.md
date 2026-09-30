# Issue #5370 T5 — bind inherited urgency to request, target, expiry, and blocker

## Disposition

`PASS_T5_INDEPENDENT_CLAIM_BINDING_ORACLE` for a synthetic finite policy model.
This is not a cryptographic, real-scheduler, or production authorization result.

## H / T / D / C / U

- **H:** An authenticated urgency number alone is insufficient for inheritance. The exact verifier request, target, expiry, and live wait-for edge must all bind to the claim.
- **T:** Exhaustively enumerate 256 combinations of those five Boolean predicates, claimed priority 1–4, and cap 2/3. Run the candidate once in Docker and an independently implemented raw-only oracle once in a separate container.
- **D:** PASS only for 256 unique rows and exact oracle agreement; inherit only when all five predicates are true; unauthorized/unbound inheritance must be zero; cap must never be exceeded.
- **C:** If the source already authenticates the urgency and guarantees request/target/freshness/blocker binding, additional enforcement would be redundant. The model treats all Boolean predicates as trusted inputs.
- **U:** No cryptography, real scheduler, distributed wait graph, clock source, starvation, GUI, or production authorization is covered.

## Frozen execution

- Base main: `2188d11aedac87d3e1e92ca25a7d1b5d4f593e90`.
- Allocation: `issue-5370-t5-bound-urgency-claim-20261001-01`.
- Candidate source SHA-256: `18d1cc5f17c3bc990869d6245b619844c87720d6708369012d0092fb66fdbe3e`.
- Independent auditor SHA-256: `77ce7d7806fa870c0c8c0a17350f85c2f8445d27cfeb481ca31f76c7d302e9a3`.
- Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Candidate: one invocation, network disabled, read-only root and source mount, 1 CPU, 256 MiB.
- Auditor: one invocation in a separate container, network disabled, read-only root and source mount, 1 CPU, 128 MiB.
- Candidate raw SHA-256: `3d6ad66e2571c2d7b7eec6357b8383d9a8e39b582a1f8cea9927f4d195b2d868`.
- Auditor output SHA-256: `7822a02a3b817c95e1393509a9b33d6bb24b14397ea62e49b22068e361c052cf`.
- Semantic payload SHA-256 independently recomputed: `ecd8ebf914c8d6f9fedf367021d5ddbf4a47978de64909ff1adab259efa977bb`.

Pre-freeze construction correction: the first draft expected eight inherited rows, while the declared finite grid yields six (claimed priority 2–4 under each of two caps). The arithmetic was corrected before source freeze and before any candidate/auditor invocation; this is not an experimental outcome.

## Result

- 256/256 input combinations were unique and independently recomputed.
- Six combinations raised priority above the base; all six had authentication, request match, target match, unexpired claim, and a live blocking edge.
- Unauthorized or unbound inheritance: 0.
- Maximum effective priority: 3, never exceeding the row's cap.
- Auditor status: `PASS_T5_INDEPENDENT_CLAIM_BINDING_ORACLE`, `errors=[]`.

The exact claim from this model is only that a conjunctive policy can enforce these finite Boolean binding rules. The input bits themselves are not authenticated or connected to an actual process/resource graph.

## Artifacts

`candidate.py`, `audit.py`, `raw.json`, `independent-audit.json`, `FREEZE.json`, `PLAN.md`, `RUN_LOG.md`, `docker-invocations.txt`, and `SHA256SUMS.txt` are retained together. No T0–T4 result was edited or rerun.
