# Issue #1839 successor A02 — audit mutation-contract result

**Disposition: `PASS_AUDIT_MUTATION_CONTRACT_SCOPED`.** The source-only candidate and independently implemented auditor agreed on the exact retained-corpus summary; all six candidate-summary corruption controls were rejected. A01's auditor STOP remains unchanged. This is an audit-implementation qualification only, not evidence that a task effect occurred.

## H / T / D / C / U

**H.** A fresh pair can reconstruct the retained source and reject six independently frozen candidate-output corruptions without promoting weak evidence or granting authority.

**T.** Intake main `b7300488efd4d27b874785bd024929c886484048`; retained raw SHA-256 `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740` (7,392 bytes). OrbStack Engine 29.4.0 linux/arm64; Python image `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; network disabled; requested 1 CPU / 512 MiB / 64 PIDs; read-only source/root. Candidate and auditor ran in separate containers, once each, no retries. The auditor reads the original source and candidate JSON directly and imports no candidate module.

**D.** Candidate exit 0; auditor exit 0. The independently reconstructed records match exactly: six sessions, 194 typed scorer samples, three attack physical DOWN/UP joins, zero attack positive endpoint sessions, zero no-input positive endpoint sessions, and zero authority grants. Corruptions `drop_session`, `duplicate_session`, `forge_effect`, `erase_physical_join`, `alter_sample_count`, and `grant_authority` were each rejected (6/6). No retries or output replacements.

**C.** This corpus contains no positive endpoint, so the experiment evaluates audit agreement and refusal boundaries only; it does not measure positive-effect sensitivity. It remains a fixed one-actuation-per-attack-session retained source, not a general multi-actuation or live integration test. A01's independent-auditor implementation failure is not erased by this successor.

**U / stop.** No positive task effect, scorer truth, causal attribution, game-control efficacy, recovery, MAP01 completion, safety, latency, human-tempo, or product claim. Stop after this one candidate/auditor pair; no live allocation follows automatically.

## Integrity and reproduction

Exact raw, candidate, audit, stdout/stderr, container receipts and SHA-256 manifest are under `results/formal-01/`. The candidate and audit outputs are preserved exactly as emitted. The audit independently reparses the hash-pinned raw source and compares the whole normalized result, then rejects six mutated copies of the candidate JSON. The local construction test is not pooled into the formal result.

## Local validation

- Construction test: 1/1 passed.
- Analysis index: 547 retained result/failure directories indexed; regression tests 6/6 passed.
- Research workspace index: 156 top-level directories reachable; tests 21/21 passed.
- `git diff --check` passed.
- GitHub Actions status is separate from these local checks and will be reported after PR delivery; no hosted PASS is inferred here.
