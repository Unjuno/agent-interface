# Issue #7501 A02 — source-bound provenance boundary

**Disposition: `PASS_PROVENANCE_BOUNDARY`.** A deterministic ten-case CPU fixture shows that a typed-clause checker can bind clauses to exact UTF-8 source byte spans, a matching document/contract revision, and a pinned immutable hard-background document before computing complete minimal conflict cores. Invalid byte digest/span/identity, stale revision, missing hard background, hard-background conflict, and unknown syntax failed closed in the declared ways. The pair conflict and two-independent-MUS cases produced exactly their complete expected core sets.

The independent assignment-enumerating auditor matched every candidate outcome and rejected all eight frozen mutation controls. Dispatch and input authority remained false in every case. Candidate and auditor each ran exactly once after a pre-run freeze; retries were zero. Full hashes and execution details are in [FREEZE.md](FREEZE.md), [RUN.md](RUN.md), [CANDIDATE.json](CANDIDATE.json), and [AUDIT.json](AUDIT.json).

## H / T / D / C / U

- **H:** Binding typed clauses to exact UTF-8 spans, source revision, and a pinned immutable background detects corrupted, duplicated, or stale provenance before SAT/MUS diagnosis; hard-background conflict blocks without offering hard clauses for relaxation or authorizing dispatch.
- **T:** Ten deterministic cases; frozen source and decision gate; one candidate invocation and one independent auditor invocation; eight in-memory mutation controls.
- **D:** `PASS_PROVENANCE_BOUNDARY` required all ten oracle matches, exact expected cores, fail-closed provenance/background/unknown cases, no authority/dispatch, and rejection of every mutation. Met.
- **C:** The checker accepts pre-authored typed clauses. Hashes establish byte identity relative to supplied bytes, not authorship or semantic fidelity. The Boolean family is tiny and constructed.
- **U:** No natural-language parsing or faithful task encoding, human explanation/restatement, comprehension, GUI, model, real contract, runtime admission, task effect, product safety, broad solver performance, or resource/memory benefit was tested. This was a CPU method run in Ubuntu WSL, not a container comparison or a migration validation.

## Outcome summary

| Outcome | Count |
|---|---:|
| SAT | 1 |
| Complete conflict-core result | 2 |
| Invalid provenance | 3 |
| Stale revision | 1 |
| Missing hard background blocked | 1 |
| Immutable-background conflict blocked | 1 |
| Unknown syntax | 1 |

This is the distinct source-provenance follow-up named by the current #7501 handoff. It does not rerun or rewrite the merged T0 or A01 scaling record. The issue remains open for the separate human-authorized restatement/explanation question; this finite method pass does not answer that question.
