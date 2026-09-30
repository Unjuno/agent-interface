# Issue #5440 T2 — sensitivity under an omitted latent-cause family

## H / T / D / C / U

**H.** A sensitivity calculation is only robust relative to its declared latent
family. Two worlds can have identical observed evidence and positive worst-case
margin within that family, while an omitted common cause reverses one world's
decision. A gate that lacks a trusted, graph-bound completeness attestation
must therefore say `UNIDENTIFIED`, not `ROBUST`.

**T.** Eight fixed paired synthetic worlds use byte-identical declared graphs
within each pair. In the complete-family member, the hidden cause is absent;
in the unverified member, an audit-only hidden cause makes the true worst-case
margin `-1/10`. Compare a T1-style declared-family-only calculation with a
coverage-aware candidate gate. Include four fail-closed controls: missing or
unverified completeness attestation, mismatched graph digest, and untrusted
issuer. Freeze the exact candidate, raw-only oracle, and input; run the
construction unit tests before freeze, then the candidate once and the
independent raw-only audit once in separate Docker Desktop containers with
network disabled and read-only source.

**D.** `PASS_T2_SYNTHETIC_SCOPE_GATING` only if all 8 complete-family rows are
ROBUST with positive exact-rational margins; all 8 unverified-family rows are
UNIDENTIFIED despite the T1-style declared-only gate falsely labeling all 8
ROBUST while the independent hidden-cause oracle finds reversal; all four
attestation controls fail closed; candidate rows, source/input/container
identities and hashes reconcile; and the independent audit has zero errors.
Any hidden-world ROBUST, robust complete-world false rejection, mismatch, or
hash drift is FAIL/STOP as appropriate; no retry under this identity.

**C.** This is a deterministic authored toy with exact rational values and an
assumed trusted completeness-verification result. It does not prove that any
real latent-family inventory is complete, validate an attestation authority,
estimate probabilities, or establish causal identification.

**U.** No real action, runtime, GUI, model, stochastic population, calibration,
or production safety is tested. A missing or dishonest completeness authority
cannot be repaired by sensitivity arithmetic; the next real evidence must
justify how a domain-specific latent-family inventory is bounded.

## Provenance and execution

This is an additive T2 successor to Issue #5440 T1, not a rerun or edit of T1.
Frozen GitHub main: `a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3`.
Docker image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
Platform: `linux/amd64`. Candidate and auditor use separate containers, each
`--network=none --read-only`; only the output directory is writable. No
network, model, GPU, X11, GUI, input, or user data is involved.

Candidate: `candidate.py` SHA-256
`5610c1aefb0a43f57c880ef08477d57eb4e97111c650c83a350e70979feadf01`.
Independent auditor: `audit.py` SHA-256
`d0a440925ae1a3a372eaf458a150ceb40fc31da3574cc07e72f682202c88317e`.
Input: `cases.json` SHA-256
`724dad606aa4bcea0b8ec47a4d0e45abbb11cc5226843f8ea62304042d691d66`.
Pre-freeze construction tests: `test_construction.py` SHA-256
`8caa6a3a99916986fc6d3d09f9ac08784849f2315c3b2ec8398aa69c119db987`;
Docker Desktop result 4/4 PASS before formal candidate execution.

The local user workspace is not a repository checkout. Exact source bytes will
be read back from GitHub before the single tree/commit/ref update. Candidate
and auditor outputs must be retained without overwriting earlier evidence.
