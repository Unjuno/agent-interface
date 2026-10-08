# Formal result — Issue #7993 T0 A01

## Disposition

**`PASS_METHOD_SCOPED` for the frozen finite-cohort follow-up-method slice.**
The formal candidate/auditor invocation completed once in WSLc. This does not
complete the broader Issue #7993 proposal or establish live verifier-risk
calibration. The issue's pre-allocation addendum also calls for evaluation
across independently generated cohorts against a declared superpopulation
risk (e.g. an IPCW target); A01 did not do that. Do not cite this result as
evidence for that broader target. A successor allocation should freeze and
evaluate that separate target before execution.

## Frozen scope and result

- Protocol: `issue-7993-t0-a01-v1`; source manifest: `FROZEN.json`.
- 25 checkpoint snapshots; candidate inputs and full-truth oracle inputs were
  separate. The candidate read no oracle file.
- The raw-only auditor reconstructed all 25 snapshots and all 16 independent
  follow-up masks. All-assigned intervals contained the finite cohort truth;
  the preregistered informative-delay witness passed; exact mean of the
  eligible Horvitz–Thompson point estimator over the 16 masks was `1/4` for
  the fixed `1/4`-risk cohort.
- Ten deliberate mutations were all rejected. Auditor `errors` was empty;
  candidate and auditor subprocess exit codes were both 0; formal WSLc exit
  code was 0. The sole formal invocation is preserved in `raw_a01/`.
- WSLc warned that swap-limit capabilities are unsupported or cgroups are not
  mounted. The requested `512M` flag therefore does not demonstrate effective
  memory-limit enforcement.

## Interpretation limits

The exact enumeration validates only the stated design-expectation identity
under the authored fixed-cohort, independent `pi=1/2` follow-up mechanism. The
point estimate is neither a bound nor a risk certificate and does not identify
the realized missing labels. The observationally equivalent hidden worlds
remain non-identifiable. No result transfers to production verifier risk,
shift, real censoring models, GUI effects, runtime safety, or action authority.

## Construction history

Pre-freeze Attempt 01 failed because one mutation control was a no-op; four of
five unit tests passed. The mutation was corrected. Attempt 02 passed all five
tests and ten effective mutation controls. Both records and captured outputs
are retained in `CONSTRUCTION_LOG.md` and `construction_a02.*.txt`; neither
was the formal candidate/auditor run.

## Formal invocation

One WSLc 3.0.1.0 invocation used cached digest-pinned Python 3.12.14 on
linux/amd64, `--pull never`, `--network none`, one CPU, requested `512M`,
read-only `/src`, and separate writable `/out`. Do not retry this frozen
formal invocation. All stdout, stderr, receipts, raw outputs and their hashes
are under `raw_a01/`; `SHA256SUMS` covers the retained package and raw evidence.
