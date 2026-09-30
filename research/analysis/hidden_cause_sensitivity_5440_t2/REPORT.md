# Issue #5440 T2 — omitted-family sensitivity gate

**Scoped result:** `PASS_T2_SYNTHETIC_SCOPE_GATING`, verified by raw-only auditor v3. The candidate was run exactly once. The initial v1 auditor FAIL and v2 auditor STOP are retained unchanged; neither caused a candidate rerun.

## H / T / D / C / U

**H — Hypothesis.** A sensitivity calculation is robust only relative to its declared latent-cause family. Identical observed evidence can have a positive declared-family worst-case margin in both a complete world and a world with an omitted common cause that reverses the result. Without trusted, graph-bound family-completeness evidence, the gate should report `UNIDENTIFIED`, not `ROBUST`.

**T — Test.** Eight paired exact-rational worlds shared the same declared graph within each pair. Each declared-only lower margin was positive. In the complete-family member, the audit oracle enumerated only the declared cause; in the unverified member, an audit-only hidden cause made the true lower margin exactly `-1/10`. The candidate never received hidden-world truth. Four attestation controls tested absent/unverified records, a wrong graph scope digest, and an untrusted issuer. Candidate and independent auditor ran in separate Docker Desktop containers.

**D — Result.** Auditor v3 matched all 20 candidate rows with zero errors: all 8 complete-family cases were `ROBUST`; all 8 unverified cases were `UNIDENTIFIED`; all 4 corrupt/missing-attestation controls were `UNIDENTIFIED`; and authority grants were zero. The declared-family-only comparator would call all 8 hidden-world cases `ROBUST` despite all 8 having a hidden-cause reversal. Decision: **PASS within the synthetic scope only**.

**C — Assumptions.** Exact authored rational values, two binary latent factors, and a synthetic completeness-verification result. The test assumes a trusted authority can establish the declared family’s completeness and bind that statement to the graph digest. This does not test the existence, trustworthiness, or cryptography of such an authority.

**U — Limits / next evidence.** This is neither causal identification nor a calibrated probability or production safety result. A real-world family-completeness claim needs a domain-specific, reviewable inventory and evidence that relevant causes are bounded; sensitivity arithmetic cannot discover an omitted cause by itself. No runtime, GUI, live action, model, or actuation was used.

## Execution and preserved audit failures

- Frozen main: `a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3`.
- Candidate invocation: one, Docker Desktop, `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `linux/amd64`, network disabled, read-only source.
- Raw SHA-256: `048e47d158dc9bacf26877a783864120398e46d8c638d416bff3760de1f3a09f`.
- Auditor v1 ran once and returned `FAIL` with `base_main_sha` and `candidate_row_18`. The frozen auditor had retained a pre-freeze main SHA and expected the wrong-scope control to overwrite the *declared graph digest* instead of only invalidating the attestation. Its source and output are preserved as `audit-v1.py` and `audit-v1.json`.
- Auditor v2 was a separate raw-only source, run once; it stopped before producing output with `KeyError: 'mode'`. Its frozen source and exact STOP are preserved as `audit-v2.py` and `audit-v2-stop.json`.
- Auditor v3 was separately frozen after 2/2 Docker construction tests. It does not import the candidate, matches its raw output to an independently enumerated exact-rational oracle, and returns PASS with zero errors. Auditor v1 and v2 outcomes were not deleted, edited, or relabeled.
- Pre-freeze candidate construction tests: 4/4 PASS. Auditor-v3 construction tests: 2/2 PASS without reading the candidate raw.
- Candidate and each audit source were invoked once per recorded identity; no retries or candidate reruns. Exact identities and digests are in `FREEZE.json`, `AUDIT_V2_FREEZE.json`, `AUDIT_V3_FREEZE.json`, and `SHA256SUMS.txt`.

## Reproduction

The candidate, case input, every auditor version, the unmodified raw and audit outputs, STOP record, freezes, test sources, and command record are retained in this directory. Do not rerun the candidate under this allocation. Any further test requires a new successor identity and must retain this result unchanged.
