# Issue #5440 T1 — multi-factor hidden-cause sensitivity gate

Status at source freeze: **CONSTRUCTION_CHECK_PASS / FORMAL_DOCKER_PENDING**. This file is the preregistration and scope contract; it is not a formal container result.

## H / T / D / C / U

- **H:** Extending the T0 one-dimensional margin to evidence graphs with shared and private latent causes can distinguish robust from sensitive nominal commits. At an explicitly matched abstention budget of 25%, the sensitivity gate should reject every claim whose declared worst-case margin is non-positive, while a margin-only provenance baseline leaves some such claims admitted.
- **T:** Evaluate 8 matched pairs (16 claims). Each graph has two attested evidence nodes, one shared-clock latent cause spanning both nodes, and two private causes. Freeze exact rational margins/weights in `cases.json`. Compare (1) provenance-only nominal admission, (2) a fixed 25% margin-only abstention baseline (lowest nominal margin, then case ID), and (3) the exact sensitivity gate. Candidate computes a closed-form rectangular worst case; a separately implemented auditor exhaustively enumerates all vertices of each three-cause uncertainty cube (8 assignments/claim). Run fixed corruption controls against the auditor.
- **D:** Scoped PASS only if all 16 candidate rows match the independent vertex oracle; exactly 4/16 claims are sensitivity-abstentions (the frozen 25% budget); the sensitivity policy leaves zero claims admitted with non-positive worst-case margin; the equal-size margin-only baseline leaves at least one such claim admitted; all mutation controls are rejected; and hashes/integrity pass. Any candidate/oracle mismatch or unsafe sensitivity admission is FAIL. If the stated gate needs more than 25% abstention or graph/provenance validity is ambiguous, disposition is UNCERTAIN.
- **C:** This is a deterministic synthetic contract test with authored monotone linear latent effects, exact rational arithmetic, attested inputs, and a rectangular uncertainty set. It does not estimate causal bias, probabilities, calibration, production safety, or real action correctness.
- **U:** Real latent-cause bounds, dependency structure, observer truth, evidence incompleteness, action-class loss, and useful live abstention budgets remain unknown. No product threshold or automatic actuation authority follows.

## Frozen comparison

All 16 nominal margins are positive and all evidence nodes are marked `ATTESTED`. Each latent variable ranges over its declared `[0,bound]`; shared causes have multiple graph edges and must be counted as one shared variable, not as independent copies. Adverse weights are non-negative. A claim is model-robust only when its minimum margin over the complete declared set is strictly positive.

The margin-only baseline abstains on exactly 4 cases selected by ascending nominal margin then lexical case ID. This fixes the comparison budget without consulting latent edges or outcomes.

## Execution boundary

Host-side construction check (not container) passed on Python 3.12.10: the frozen candidate's 16 rows matched an independently implemented exact-rational enumeration of all 128 latent-cube vertices; the 25% matched-budget gate yielded 4 sensitivity abstentions, 2 residual unsafe admissions for the margin-only baseline, and 0 for the sensitivity gate. Reproducer and scope are in `construction_oracle.py` and `construction-result.json`. An earlier host wrapper attempt wrote a raw file with injected container metadata; it was caught before audit and deleted, and is explicitly excluded from evidence.

The local Docker Desktop lane remains unused because current #5085 still records no exact owner-confirmed exclusive local lease. The formal workflow runs on a `main` push that changes the frozen candidate/input/auditor/preflight/workflow paths. If no run appears for that source commit, the same workflow can be manually dispatched once; check run history first to prevent duplication. It uses a digest-pinned hosted Docker container with `--network none`, read-only source, and a separate output mount. This is hosted Docker, not Docker Desktop. It executes the candidate once, independent raw-only audit, and corruption controls, then uploads the raw output and source hash manifest. A later results PR is checked by a separate audit-only workflow without rerunning the candidate. No formal T1 conclusion is claimed until that hosted artifact and committed-evidence audit are both read back.

Base main at source freeze: `ffb0d43b5f0408011a3f70223da43d4aa3f27fe4`.
