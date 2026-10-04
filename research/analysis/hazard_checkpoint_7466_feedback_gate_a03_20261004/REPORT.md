# Issue #7466 A03 — sequential evidence gate result

## Scope and question

This frozen synthetic successor tests whether requiring fresh, within-episode evidence before enabling adaptive checkpoint placement can avoid adaptation on independent/reversed signals while preserving a useful cost reduction on held-out informative signals. It does not modify or regrade A02 or the earlier A01 result. The exact hypothesis, protocol, and limits are in [README.md](README.md); the frozen parameters and hashes are in [FREEZE.json](FREEZE.json).

## Decision

**`FAIL_UNSAFE_RESUME` under the frozen auditor.** This is a finite synthetic-policy failure, not evidence of a production or real-interface defect.

The candidate and independent auditor were each invoked once with zero retries. The candidate exited 0, produced 432 episodes and 669,050 streamed ticks, and passed its calibration gate. The auditor exited 0 with no reconstruction errors, reconstructed all 432 rows / 669,050 ticks, and rejected all four mutation controls. Source/input hashes match the freeze. See [RUN.md](RUN.md) and the raw outputs under [formal_01](formal_01/).

The safety/benefit gates did not pass:

- All 144 reversed-cohort episodes are incomplete (24 in each of six cost cells); no cell meets exact completion/effects. The adaptive policy did abstain on every independent and reversed trace and matched the event-boundary decisions, but abstention alone does not satisfy exact task completion.
- Informative benefit is not robust across the frozen cost matrix. At checkpoint/replay costs 4/1, candidate median cost is 375.5 versus fixed 351.0 (6.98% worse). At 8/1 it is 948.0 versus fixed 423.0 (124.11% worse) and event 517.0 (83.37% worse). Those cells fail the required 10% improvement against both baselines.
- The other informative cells do improve, sometimes substantially, but the preregistered requirement is every cell, so aggregate/selective wins cannot change disposition.

The candidate was held out of independent/reversed adaptation successfully, but its event fallback plus the chosen 300-unit task and 3,000-tick horizon did not complete the reversed cohort. The gate therefore correctly rejects the overall policy; do not describe this as a clean safety pass or efficacy result.

## Reproducibility and retained evidence

- Freeze SHA: base `bb3138d019118bf050fe1136a9ba3619146bb46e`; frozen source and input hashes are in `FREEZE.json`.
- Formal raw candidate: `formal_01/candidate.json` (314,596,618 bytes; SHA-256 `afaf783f1f8f8e5f7c4ee93661e27f8962a0c883456650531278de901bd3135f`). `candidate.json.gz` (18,362,497 bytes; SHA-256 `b391bc0edb3799a6ad0badf7b9f2abe23457b55d13277dc51b477b7abdd6cdb7`) is a lossless transport copy; verify by decompressing and comparing the raw hash before audit replay. The uncompressed raw is retained locally and should not be pushed as a Git blob.
- Independent audit: `formal_01/audit.json`, SHA-256 `db12c161c0ad9c65876d80af6b8a9adce9efcffb4d63fe1d32d463ff88bb4d88`; stdout record: `formal_01/audit.stdout.json`.
- The independent audit's clairvoyant finite-horizon lower bound is reported as zero for every cell. Treat that diagnostic as non-informative, not as a useful optimality comparison; it does not affect the frozen candidate-vs-baseline gates or disposition.
- Candidate and auditor ran on host CPython because this protocol is standard-library-only and the declared local container image was absent. No model, GUI, human, provider, real interruption process, semantic checkpoint persistence, or production latency was tested.

## Follow-up boundary

Do not rerun this freeze or edit its source/results. A distinct successor may be warranted to test the cost-sensitive policy and task/horizon feasibility with a computationally bounded independent oracle, after checking current issue/roadmap ownership and avoiding reuse of these seeds. Any such work must preserve this FAIL result as-is and independently freeze new sources, inputs, seeds, and gates before execution.
