# Issue #5440 T1 — multi-factor hidden-cause sensitivity gate

Status at source freeze: **EXPERIMENT_PENDING**. This file is the preregistration and scope contract; it is not a result.

## H / T / D / C / U

- **H:** Extending the T0 one-dimensional margin to evidence graphs with shared and private latent causes can distinguish robust from sensitive nominal commits. At an explicitly matched abstention budget of 25%, the sensitivity gate should reject every claim whose declared worst-case margin is non-positive, while a margin-only provenance baseline leaves some such claims admitted.
- **T:** Evaluate 8 matched pairs (16 claims). Each graph has two attested evidence nodes, one shared-clock latent cause spanning both nodes, and two private causes. Freeze exact rational margins/weights in \`cases.json\`. Compare (1) provenance-only nominal admission, (2) a fixed 25% margin-only abstention baseline (lowest nominal margin, then case ID), and (3) the exact sensitivity gate. Candidate computes a closed-form rectangular worst case; a separately implemented auditor exhaustively enumerates all vertices of each three-cause uncertainty cube (8 assignments/claim). Run fixed corruption controls against the auditor.
- **D:** Scoped PASS only if all 16 candidate rows match the independent vertex oracle; exactly 4/16 claims are sensitivity-abstentions (the frozen 25% budget); the sensitivity policy leaves zero claims admitted with non-positive worst-case margin; the equal-size margin-only baseline leaves at least one such claim admitted; all mutation controls are rejected; and hashes/integrity pass. Any candidate/oracle mismatch or unsafe sensitivity admission is FAIL. If the stated gate needs more than 25% abstention or graph/provenance validity is ambiguous, disposition is UNCERTAIN.
- **C:** This is a deterministic synthetic contract test with authored monotone linear latent effects, exact rational arithmetic, attested inputs, and a rectangular uncertainty set. It does not estimate causal bias, probabilities, calibration, production safety, or real action correctness.
- **U:** Real latent-cause bounds, dependency structure, observer truth, evidence incompleteness, action-class loss, and useful live abstention budgets remain unknown. No product threshold or automatic actuation authority follows.

## Frozen comparison

All 16 nominal margins are positive and all evidence nodes are marked \`ATTESTED\`. Each latent variable ranges over its declared \`[0,bound]\`; shared causes have multiple graph edges and must be counted as one shared variable, not as independent copies. Adverse weights are non-negative. A claim is model-robust only when its minimum margin over the complete declared set is strictly positive.

The margin-only baseline abstains on exactly 4 cases selected by ascending nominal margin then lexical case ID. This fixes the comparison budget without consulting latent edges or outcomes.

## Execution boundary

The local Docker Desktop lane is not used: current #5085 records no exact owner-confirmed local Docker/OrbStack lease, and #5411/#5360 have separate queued CPU requests. This rung uses a hosted GitHub Actions Ubuntu runner running a digest-pinned Docker container with \`--network none\`, read-only source, and a separate output mount. This is Docker container execution, not a claim of Docker Desktop execution.

The run workflow executes the frozen candidate once, then the independent raw-only auditor and corruption controls, and uploads raw JSON + hash manifest. A separate audit-only workflow validates the committed output without rerunning the candidate. No claim is made until the output artifact and final PR checks are read back.

Base main at source freeze: \`cbca212667bc0c256184ef71bd8c1000d8c9a8aa\`.
