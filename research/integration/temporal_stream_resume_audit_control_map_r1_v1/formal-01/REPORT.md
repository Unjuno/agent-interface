# #4534 corrected control-map audit — HOLD

Allocation: `temporal-resume-control-map-20260927-01`

Frozen source/gate commit: `d3cd713e6b2adad865367f5b4ff4b82afc42b93c`

Input #4447 commit: `de1064b335a6567c57817209485cf18d25d9e3f2`

Input formal manifest SHA-256: `1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855`

## Disposition

`HOLD_POSITIVE_CONTROL_CLEANUP_RECEIPT`. The frozen verifier ran exactly once in local Docker and returned outer exit 1. No rerun, source edit, gate adjustment or result substitution followed.

The baseline audit returned 0 with 54 rows, 48 candidate matches, 40 comparator disagreements, six corruption refusals and no errors. The source and original evidence tree hashes matched before/after. All eleven byte-changing controls were rejected, including the corrected #4447 `control_accept` mutation targeting case_id 48 (BATCH5 row 3, `foreign_epoch`, original candidate `REFUSE_CHECKPOINT` changed to `OK`). The separate no-change positive control was byte-identical and accepted (verifier return 0). Thus the corrected control map closes #4511's missing-effective-mutation gap in this scoped copied-evidence outcome.

The remaining frozen gate failure is cleanup evidence. `run_control_map.py` sampled `positive_control.copy_removed` while still inside the `TemporaryDirectory` context, so the retained output says `false` and the runner exits 1. The file does not contain a post-context removal receipt. Even though the context manager is designed to clean up at exit, this allocation's frozen D gate requires recorded proof; it therefore remains HOLD. The mutation copies each recorded `copy_removed=true`. Do not reinterpret the successful mutations as a formal PASS.

## Execution and incident record

- Successful run: local Docker Desktop Engine 29.8.0, `python:3.13.5-slim-bookworm`, image `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, `linux/amd64`, `--pull=never --network none --read-only`, bounded tmpfs. Source, evidence and verifier mounts were read-only; `/results` was the only writable mount.
- One earlier host path-resolution attempt stopped before container creation (Docker exit 125); retained in PREFLIGHT01. It did not consume the formal verifier invocation.
- Frozen post-readback synthetic tests passed 3/3 in local Docker without mounting #4447 evidence.
- #4447 source/evidence and #4511 verifier were not changed. #4447 and #4511 dispositions remain unchanged.

## H / T / D / C / U

- **H:** Correctly addressing the case_id 48 corruption control restores the missing original mutation; the #4511 verifier rejects it and all other tested receipt mutations.
- **T:** One deterministic baseline audit, eleven changed mutation copies, and one unchanged positive acceptance copy over retained evidence only. No temporal scientific cases were rerun.
- **D:** HOLD. All 11 mutations rejected and positive control accepted, but its frozen cleanup receipt is false because measured before context exit; complete D requires retained cleanup proof.
- **C:** Same-author offline copied-evidence audit. Controls are targeted verifier tests, not independent review or prevalence evidence.
- **U:** Does not upgrade #4447/#4511, resolve predecessor fixture identity or Docker kernel equivalence, or establish production behavior, durability or performance.

`BASE_AUDIT.json`, `CONTROL_RESULTS.json`, `EXECUTION_ENVIRONMENT.json`, `OUTER_RUN.json`, `OUTER_RUN.log`, and PREFLIGHT01 preserve the formal output, exact outcome and earlier no-container stop. ARTIFACT_MANIFEST.json binds these artifacts.
