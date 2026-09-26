# #4511 formal audit — HOLD

Allocation: `temporal-resume-audit-returncode-20260927-01`

Frozen verifier commit: `3a5557245fd1f57e9d65e9ddfd732d67abd41b69`

Input #4447 evidence commit: `de1064b335a6567c57817209485cf18d25d9e3f2`

Input artifact manifest SHA-256: `1584edb3a45202b3e816d2a9735708265dae279fd4e18d8680fded7756cc3855`

## Disposition

`HOLD_GATE_CONTROL_DENOMINATOR`. The once-only frozen local Docker run's outer exit was 1. Do not interpret this as a verifier PASS. No rerun, threshold adjustment, source patch, or replacement outcome was performed.

The baseline verifier itself returned 0 with 54 rows, 48 independently checked candidate cutpoints, 40 comparator disagreements, six corruption refusals, six Docker batch receipts, and no audit errors. Source/evidence tree hashes matched before and after.

The results expose a fixed-gate design error. The eleven named cases are ten corruptions plus `control_accept`, which deliberately rewrites a field to its existing value. Therefore `control_accept` is byte-identical, correctly accepted, and is not a mutation. Nine of the other ten byte-changing corruptions were rejected; the added comparator-returncode mutation was also rejected. In total, ten byte-changing mutations were rejected. But the frozen code computes `effective = bytes_changed && rejected` and requires `effective == 11`, so it exits 1. This is neither evidence that the verifier misses the comparator receipt nor a valid 11-mutation pass: the advertised denominator conflates ten mutations and one negative-control acceptance. Under the frozen decision gate this is HOLD.

No scientific cases were rerun. The #4447 HOLD remains unchanged. The #4511 result does show, in this scoped copied-evidence audit, that candidate, prepare, and comparator nonzero receipt mutations were rejected while the acceptance control was accepted.

## Environment and lineage

- Execution: local Docker Desktop only; `python:3.13.5-slim-bookworm`, `linux/amd64`, Docker Engine 29.8.0, `--pull=never --network none --read-only`.
- Frozen #4447 source: 14 manifest entries verified before the container invocation; source and evidence mounted read-only.
- The three pre-verifier execution incidents are retained as PREFLIGHT01–03. They occurred before any formal verifier invocation. The exact r1/r2 scratch receipts remain preserved outside this repository; PREFLIGHT02/03 logs are copied here. PREFLIGHT01 remains at the frozen source path and is listed in FREEZE_REV02.
- Construction failures and subsequent synthetic-only 5/5 results remain in CONSTRUCTION01–05; none mounted #4447 evidence.
- Prior #4447 trial, byte-identity caveat, and disposition are untouched.

## H / T / D / C / U

- **H:** Raw child receipt checks reject the candidate/prepare/comparator nonzero-return-code mutations under copied-evidence tampering.
- **T:** Frozen verifier ran once against the fixed 54-row evidence and eleven named cases; no new scientific trial.
- **D:** HOLD, because the immutable gate requires eleven byte-changing rejected mutations, but the frozen control set contains only ten mutations plus one unchanged accepting control (effective=10, Docker exit=1).
- **C:** Same-author, offline, deterministic audit of retained evidence; targeted mutations are verifier controls, not prevalence estimates or independent review.
- **U:** Does not establish exact predecessor fixture identity, platform equivalence, durability, production behavior, or performance; does not upgrade #4447.

## Retained files

`BASE_AUDIT.json`, `CONTROL_RESULTS.json`, `EXECUTION_ENVIRONMENT.json`, `OUTER_VERIFY.json`, and `OUTER_VERIFY.log` retain the actual output/receipt. PREFLIGHT02/03 preserve two pre-invocation failures; PREFLIGHT01 and CONSTRUCTION01–05 are retained with the frozen source. `ARTIFACT_MANIFEST.json` binds the committed formal bundle.
