# Issue #1839 successor A01 — execution STOP

**Disposition: `HOLD_AUDITOR_NOT_COMPLETED`.** This is an execution/instrumentation STOP, not a task-effect finding. The candidate completed once; the frozen independent auditor failed before it produced an audit summary. No PASS or candidate/auditor agreement is claimed.

## H / T / D / C / U

**H.** A source-only independent audit of the retained #4193 corpus can preserve the no-positive-endpoint state as `UNRESOLVED_NO_TASK_EFFECT`, without granting authority, while rejecting six frozen absence/misattribution probes.

**T.** Intake main `6fdfa6b2e2bbb13a58a235dae5499676d7dd417f`; compressed raw source SHA-256 `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740` (7,392 bytes); OrbStack Engine 29.4.0, linux/arm64; image `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; network disabled, requested 1 CPU / 512 MiB / 64 PIDs, read-only source/root. One candidate container and one separate auditor container were invoked; retries=0. Exact commands and raw streams are summarized in `results/formal-01/*.container.json`, `*.stdout.txt`, and `*.stderr.txt`.

**D.** Candidate exit 0, emitted 6 sessions / 194 samples / 3 attack physical joins / 0 positive endpoint sessions / 0 authority grants. Auditor exit 1 on the first frozen `ghost_actuation` probe: `mutate()` fell through to `AssertionError('ghost_actuation')`; no audit summary was emitted. Therefore all candidate observations remain unaudited for this allocation and the preregistered gate is unmet. `STOP.json` preserves the first disposition. No retry, source correction, or outcome relabeling occurred.

**C.** The candidate output is descriptive raw-derived output only. It does not validate the classifier, evidence semantics, task effects, or the historical malformed #4193 v3 result. The candidate dry preview and test suite were construction checks, not part of the formal denominator. The shared `unjuno-native-ci-6092` container was not touched.

**U / stop.** No positive task effect, causal attribution, scorer truth, MAP01 efficacy, recovery, safety, latency, human-tempo, or product claim. A corrected auditor requires a distinct additive successor with its own pre-run freeze and allocation; this A01 must not be rerun.

## Outcome identity

- Candidate result: SHA-256 `12685056d0be30889d38392c26718488e053d6f32a34aa89fe0ff8eeb57c85ca`.
- Auditor stderr: SHA-256 `aea48b5add0316a4f0b4acd0d5dac3f1a0bb88e993c49a0bffefcc4a0f22e19c`.
- Candidate/auditor formal counts: 1 / 1; retries 0.
- All source, package, output, and receipt hashes are in `SHA256SUMS.txt`.

## Local validation and CI boundary

- A pre-freeze host preview emitted the same six-session/194-sample summary; it is construction only and excluded from the formal allocation.
- Package unit tests: 3/3 passed. Analysis-index check: 547 retained result/failure directories indexed; its six regression tests passed. Research workspace check: 156 top-level directories reachable; workspace tests 21/21 passed. `git diff --check` passed.
- The full current Analysis Index workflow test command set was exercised locally. The geometry-feasibility group has two failures because its frozen fixture expects SHA-256 `b19000…f7c2` for `.github/workflows/analysis-index.yml`, while current main's file hashes to `a75cbd…679a`. The workflow itself restores the historically pinned file from commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` before running; independently hashing that Git object yields the expected `b19000…f7c2`. Thus the local direct-worktree invocation is not an exact emulation of the workflow's restore step; this is recorded as local CI qualification, not a product-code failure or green full-suite claim.
- One additional test command initially used the wrong discovery directory; it was rerun from the workflow's declared working directory and passed. The workflow's other included test groups completed successfully in the local run. No GitHub Actions status is represented as local verification.
