# H / T / D / C / U — #5215 audit-integrity successor

Successor audit-only validation for Issue #5215 and merged PR #5216. The original probe, plan, and scientific record remain immutable. The retained auditor accepted missing/null/string negative fields, classified evidence by booleans rather than recomputing timestamp conditions, and conflicted with its frozen plan. This successor tests the audit boundary against the exact published record; it does not repeat the kernel experiment.

**H.** Required fields and exact types can be enforced, timestamp/release inequalities independently derived, and malformed or contradictory evidence kept out of PASS.

**T.** Input: #5216 `probe-output.json`, Git blob `d3964da3cbf6524c8193b5a59ed16bdb3611772f`. The independent standard-library auditor derives case validity from a frozen integer-fact table. Mutations cover each of four negative fields missing/null/string/integer, unexpected key, identity-negative reversal, non-object record, and each case outcome flipped against the derived expectation. No kernel import/run, runtime change, model, GPU/CUDA, GUI/input, provider, or network experiment. Initial test-oracle failure (6 assertions) remains in `FAILURES.json`.

**D.** Host suite and pinned-container replay each pass 8/8 tests. The exact census rejects 18 schema/identity mutations plus eight per-case outcome flips. The immutable historical record is `HOLD_LEGACY_PLAN_CONFLICT`, with five evidence inconsistencies: execution ends 999/1000/1001 have release timestamp 800; effect observations 499/699 precede execution start/end; and the old PLAN rejects effect_at_700 while the old auditor accepted it. This is evidence-quality disposition, not a new kernel result.

**C.** Every mutation starts from the same record; each case outcome is checked against integer comparisons and release ordering. The auditor imports neither the prior probe nor kernel. The original record is read-only.

**U.** One synthetic retained record, one host, one container image. No actual OS lease enforcement, clock comparability, live effects, or production claim.

Host verification: Windows CPython 3.11.9, `python -m unittest discover -s <local-evidence-dir> -p 'test_*.py' -v`, 8/8. The exact files were fetched by immutable commit `19cc36b996e0e6a1290bd4e0c0b62db5fa2b1428`; SHA-256 auditor `e97d564936a4d5087b37317a9e04a0702834286d258020c9864a8a193f40732b`, tests `0287d4286aad5cf0f74e031b24873f65c4df568de6ef6682973fa75184e2282a`.

Container verification: Docker Desktop linux/amd64, image `python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9`; network none, read-only root and source mount, 1 CPU, 256 MiB, 32 PID cap, no-new-privileges, all capabilities dropped, 16 MiB tmpfs. Exact command: `docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --pids-limit 32 --cpus 1 --memory 256m --security-opt no-new-privileges --cap-drop ALL --mount type=bind,source=<verified-dir>,target=/work,readonly --workdir /work python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9 python -B -m unittest discover -s /work -p 'test_*.py' -v`. Exit 0; 8/8 passed.


## Coordination hold

After the pinned container replay, I fetched the current #5085 comment stream and found existing comment #5864690783 prohibiting Docker CLI use (including inspection) until an exact assignment and owner/resource release. I had checked the issue body but not its comments before launch, so the one CPU-only container run occurred out of sequence. The run is disclosed in #5085 comment #5865679335. It was not authorized by the GPU queue and is retained as a governance violation, not as resource clearance. PR #5228 is back in Draft. No further Docker/GPU calls will be made before an explicit lease/resource release.
