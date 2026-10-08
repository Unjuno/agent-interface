# Issue #4986 Stage 1 — execution result

## H / T / D / C / U

**H.** Against the same immutable role-skill package, publication only after complete validation prevents any shadow query from observing an unvalidated candidate; publication at validation start exposes it during the injected delay.

**T.** Executed the pre-registered two-arm schedule without changing inputs or thresholds: eight reader threads across eight synchronized waves per arm (64 queries/arm; 128 total). The first four waves ran during four fixed 10 ms validation-delay intervals. The unsafe diagnostic arm published early; the candidate arm kept the old package active until the validation receipt was bound. The runner executed once; the independent raw-only audit ran once in a separate container. Zero dispatches. No retries.

**D.** `PASS_ATOMIC_SKILL_PUBLICATION_SCOPED`. The auditor reconstructed all 128 rows with zero errors. In the safe `PUBLISH_AFTER_VALIDATION` arm, 0 candidate reads occurred before validation and all 32 post-validation reads observed the candidate. In the unsafe diagnostic arm, 32 pre-validation reads observed the candidate, followed by 32 post-validation reads. All six corruption controls were rejected: missing query, early candidate, dispatch, torn digest, wrong receipt, and wrong wave schedule. Runner exit code was 0.

## C — execution environment and evidence

Docker Desktop local Engine 28.5.1, `linux/amd64`, pinned image `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; network disabled, read-only root and source, one CPU, 512 MiB memory, 64 PIDs. Runner output used a fresh dedicated writable mount. The auditor consumed the resulting raw file read-only in a separate container and wrote to its own fresh output mount.

- Frozen allocation: `FREEZE.json`; sidecar `FREEZE.sha256` is unchanged.
- Raw runner output: `raw/raw.json`, 52,763 bytes, SHA-256 `c1b3ec7419bff1daea1d1b6ccf93ebccfe23f2298efdc8d3f7c7473abd64a905`.
- Independent audit: `audit/audit.json`, 624 bytes, SHA-256 `a68fc20dd08340aed20a3f261247bf721aa5a6cfe10f1c3e0f06d477e973884a`.
- Machine-readable summary: `RESULTS.json`.

No formal-run failure, retry, timeout, or stop condition occurred. The six corrupted audit fixtures were designed controls, not retries. No unplanned rerun or post-result threshold change was made. Pre-registered commands, source/input digests, and detailed limitations remain in `FREEZE.json` and `PREREGISTRATION.md`.

## U — limits

This supports only the scoped in-process synchronized Python-thread publication observation. It does not establish general filesystem/process crash consistency, cross-process or cross-host memory ordering, real Needle/Astra adaptation, learned competence, application effect, latency benefit, production safety, or product readiness. The unsafe diagnostic arm is not an execution route. No product behavior was changed by this experiment.
