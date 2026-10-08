# Issue #8583 T0 A01 — finite principal-stratum bounds

## H/T/D/C/U

- **H:** Policy-specific recovery contrasts can differ from the finite-population effect among units that would demand recovery under either policy; observed margins alone need not identify that always-demand effect.
- **T:** Exhaustively enumerate every unlabeled latent binary table compatible with four tiny, hand-authored policy-demand and recovery-success margin fixtures. Report exact rational bounds over nonempty always-demand strata and separately flag any compatible empty stratum.
- **D:** Deterministic local CPU computation in one WSLc container, Python 3.12 slim image; no network, GPU, model, GUI, people, application, or external service.
- **C:** Compare against a separately implemented ordered-assignment oracle, frozen hand-derived expectations, source/data hashes, and five frozen candidate mutations.
- **U:** Only these finite synthetic margins. No sampling uncertainty, empirical causal inference, monotonicity, exclusion restriction, cross-world assumption, real recovery effect, or product claim.

## Frozen allocation and procedure

Allocation `T0-A01`, selected as an additive successor to Issues #8569/#5760 and tracked at #8583. Freeze includes `candidate.py`, `auditor.py`, both tests, `input.json`, `truth.json`, `README.md`, `PROTOCOL.md`, and `CONSTRUCTION_LOG.md`. The fixture has N=2 or 3 and enumerates all 25 legal binary per-unit latent types; the candidate uses multisets and the independent oracle uses ordered products followed by canonicalization. Outcomes outside policy-specific demand are represented only as JSON null.

Before formal execution: run the whole package test suite in normal and optimized Python modes; verify the frozen manifest and image identity; ensure formal output paths do not exist; commit the freeze. Then execute the candidate once. Only if it exits zero, execute the independent auditor once. Outputs are exclusive-create; any launch/runtime/audit failure is retained as the terminal first outcome and is never retried or relabeled.

Stop boundaries: malformed/infeasible fixture, changed frozen digest, missing image, preexisting result path, nonzero candidate, nonzero auditor, or any independent reconstruction/mutation failure. Construction tests are not formal results.

## Decision gates

`PASS_METHOD_SCOPED` requires every compatible table to be independently reconstructed exactly, all frozen hand-derived values to match, zero reconstruction errors, and all five mutations to be rejected. Otherwise report the exact first STOP/FAIL; no retry. A PASS applies only to the frozen finite enumeration method and fixtures.

## Provenance

Runtime: Microsoft WSLc (not Docker Desktop), `python:3.12-slim`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14, linux/amd64. WSLc reports version 3.0.1.0. The host may not enforce configured CPU/memory limits; this allocation makes no resource-enforcement claim. Formal invocation and exact frozen digests are recorded in `REPORT.md` and `SHA256SUMS`.

