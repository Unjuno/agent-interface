# Issue #3311 historical source provenance successor audit

This additive study addresses the CI-only provenance blocker recorded on Issue #3311: historical source commits used by retained synthetic runs were unavailable to clean GitHub Actions checkouts, so `git show` could not independently reproduce their recorded source hashes. Existing Issue #3311 raw evidence, v1 auditor, and reports remain unchanged.

## H — hypothesis

Bundling the exact broker, runner, and test source bytes for each retained source revision will make the three v1 synthetic transport audits reproducible without Git object lookup, while preserving all previously reported semantic and raw-manifest checks.

## T — bounded test

Bundle the three historical source files for each of the three recorded commits (nine files total), requiring each SHA-256 to match the original run's `source-sha256.json`. Copy the three retained evidence roots byte-for-byte by their manifests. Adapt the frozen v1 audit only at its source-hash resolver. Run four offline controls (all source hashes, unknown revision rejection, unbundled path rejection, no Git subprocess) and then one read-only Docker invocation with `--network none` across all three evidence roots. Do not start broker, runner, model, GUI, or task workloads.

## D — decision rule

PASS only if all nine source bytes match the historical run manifests, the three copied raw manifests match the original manifests, all four synthetic controls pass, and all three container audit reports retain `PASS_V1_SYNTHETIC_TRANSPORT_ONLY` with every legacy check true. Missing/corrupt sources or evidence, a Git invocation, any false semantic check, or a container failure is FAIL/HOLD; no repair or rerun after formal invocation.

## C — controls and custody

The old experiment directory and reports are not edited. The bundled v1 auditor is a frozen byte copy. Snapshot resolution fails closed. Audit container uses the local pinned-by-ID `python:3.11-bookworm` image with network disabled and study mount read-only. Preformal unit tests are controls, not experiment outcomes. Formal image ID, frozen code/source hashes, invocation command, exit status, and complete reports are retained below.

## U — uncertainty and scope

This can establish source-provenance reproducibility and revalidate retained synthetic CLI-transport evidence only. It cannot establish a real provider/model call, live integrated cold/warm/invalidation/repair behavior, usage accounting, GUI or task correctness, host portability, or efficiency improvement. Issue #3311's integrated matched-condition experiment remains pending.

## H/T/D/C/U disposition

`PASS_SOURCE_PROVENANCE_REAUDIT` for the bounded provenance question: one formal Docker invocation (network disabled, study read-only) returned three `PASS_V1_SYNTHETIC_TRANSPORT_ONLY` reports, each with 18/18 checks true. All nine source snapshots match their original recorded SHA-256 values; all three copied raw and source manifests are byte-identical to the original manifests. The four preformal controls passed. Full reports are in `audit_reports/`; execution metadata and their hashes are in `RESULT.json`. No retry was needed. Issue #3311's live integrated cold/warm/invalidation/repair comparison remains unrun and is still the next substantive research gate.
