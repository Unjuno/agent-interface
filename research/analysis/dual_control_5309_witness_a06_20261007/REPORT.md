# Issue #5309 A06 — computation PASS, method FAIL: candidate truth leakage

## Disposition

`FAIL_METHOD_CANDIDATE_TRUTH_LEAKAGE`. The frozen computation completed and its raw-only audit passed, but the candidate was not isolated from the oracle truth table. Therefore A06 does **not** validly test the preregistered hypothesis and cannot be counted as evidence that witness-aware action ranking works. Preserve the raw PASS and the method failure together; do not rerun either formal command.

## Frozen question and gate

Allocation `5309-WITNESS-A06-ORBSTACK-20261007`, Issue [#5309](https://github.com/Unjuno/agent-interface/issues/5309), main `3dba6c86f212c37a2d80c844b816c38921a42cc5`. H/T/D/C/U and exact source/image/environment hashes are in [PRE_RUN.md](PRE_RUN.md), registered before execution in the Issue. Container: OrbStack Docker 29.4.0, linux/arm64, Python 3.14.5, pinned image `python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`; network disabled, read-only root, one CPU, 256 MiB, no extra capabilities, allocation directory as the sole writable mount.

The candidate was invoked once and exited 0. The independent auditor was invoked once and exited 0. No retries.

## Retained outputs

- Raw: [candidate-raw.json](candidate-raw.json), SHA-256 `5e7a1cc78d9c37bdf9880eaf1dd71b8badc0671c3dcd3c234aaefd4e0d0d6f16`.
- Audit: [audit.json](audit.json), SHA-256 `232be72f8c1521092d8e53e938a22c396631bbe82e46775828ba7f4e3b79e72e`.
- Auditor result: `PASS_WITNESS_BOUNDARY_SCOPED`, 56 rows, zero errors, zero authority grants; candidate raw hash matched.
- Primary hidden-a: both rankers exposed the same two-action admitted set. GENERIC_IG selected `a-progress-witness-loss` and returned `UNKNOWN_EFFECT_WITNESS_LOST`; WITNESS_AWARE selected `b-progress-preserve-witness` and returned `COMPLETE`.
- Controls: pre-existing witness completed without an extra action; no-path, stale-receipt, model-mismatch and fail-closed returned UNKNOWN; duplicate identity was consumed once; urgent stop returned `STOP_AND_RELEASE` before commit. Each scenario covers both authored states.
- Pre-freeze construction suite: 5/5 tests passed, including six corruption probes. This is construction evidence, separate from the raw-only formal audit.

## Method defect and why the hypothesis is untested

Post-run source inspection found `truth = fixture["truth"][state]` in `candidate.py`; the candidate directly reads the oracle mapping to select the commit and effect ID. The preregistration explicitly states the candidate must never see truth. In addition, the same full fixture file containing truth was mounted into the candidate container as a writable allocation directory. The auditor's raw-only reconstruction cannot prove that the candidate's completion was based only on observations. This invalidates the causal interpretation of the primary contrast despite the exact finite trace reconstruction.

No GUI, model, live input, runtime, user task, natural frequency, product benefit, or physical-release claim is supported. A04 remains `STOP_MAIN_ADVANCED_AFTER_FREEZE`; A05 remains a pre-start Docker mount-syntax STOP. Both are preserved unchanged and not rerun.

## Next method gate

Any successor must separate candidate-visible observation bytes from auditor-only oracle bytes at both the file and container-mount boundary. The candidate should receive no hidden-state label/truth mapping; its runner should consume only a candidate-input document and emit to a separate output mount. The auditor should receive the oracle independently and reconstruct the candidate's selected action, observed receipt, effect, and commit. Freeze a new allocation and hashes before running either formal process.
