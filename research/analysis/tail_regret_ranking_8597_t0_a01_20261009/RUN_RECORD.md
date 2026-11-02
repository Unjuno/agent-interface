# Run record — Issue #8597 T0 A01

- Allocation: `TAIL-REGRET-8597-T0-A01-20261009`
- Source freeze: `43c730b9192cf972453454335248d50d29ab093c`
- Base main: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`
- Platform: Python 3.14.5; Darwin 27.0.0; arm64.
- Container: none; no container requirement for finite stdlib-only host-CPU computation.

## Formal commands

1. `python3 -B candidate.py --dir .` — exactly once; exit 0; stdout `CANDIDATE_COMPLETE opportunities=24 rows=288`; start `2026-10-08T20:47:33Z`; end `2026-10-08T20:47:34Z`.
2. `python3 -B audit.py --dir .` — exactly once; exit 0; stdout `PASS_METHOD_SCOPED opportunities=24 errors=0 mutations=6/6`; start `2026-10-08T20:47:36Z`; end `2026-10-08T20:47:36Z`.

No formal command retries or reruns occurred. Construction tests are separate from formal invocation counts.

The independent auditor consumes `visible.json`, `truth.json`, and the saved `candidate_raw.json`. It does not import or execute candidate code. The output includes exact route/opportunity loss reconstruction, stratified and pooled metrics, and deterministic delete-one-cluster descriptive ranges. All files are covered by `SHA256SUMS.txt`.
