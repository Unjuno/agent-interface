# Predicate-order selectivity-drift successor (#4733)

This is a new deterministic finite sensitivity study following the scoped PASS in #4258. It asks where that frozen cost/selectivity order stops saving cost as probability mass moves from an early reject to a late reject. It does not rerun or modify #4258.

## H/T/D/C/U

- **H:** the fixed cost/selectivity order remains semantically exact but crosses above the authored naive order under the declared selectivity drift grid.
- **T:** enumerate all 16 four-Boolean truth states at 21 mass-transfer points (`alpha=0..1` by `.05`), with costs A/B/C/D=`1/2/5/10`, naive order D,C,B,A and frozen order A,B,C,D. `alpha` transfers 0.8 probability mass between A-only-false and D-only-false strata; 0.2 all-true mass stays fixed. Both policies short-circuit conjunction.
- **D:** exact truth/cost/evaluation/p50/p95/p99 reconstruction; independent raw-only audit; 5 non-vacuous corruption controls. Record the first grid point where the frozen order's expected cost exceeds naive. The pre-registered JSON is `FREEZE.json`.
- **C:** authored synthetic strata, deterministic cost units, finite grid, no parallel overlap.
- **U:** no real latency/provider/GUI/action authority, arbitrary drift guarantees, adaptation, or runtime promotion.

The Python scripts are stdlib-only and run in the already-cached Python 3.12.14 Linux/amd64 Docker image with `--network none`, read-only root/source, and separate raw/audit output. A 5-test construction smoke is excluded from the formal result.

See [`RESULT.md`](RESULT.md) for the one-shot formal outcome. Lossless raw and audit files are in `RAW_AND_AUDIT.zip.base64`; decode the base64 to a ZIP, then extract `RAW.json` and `AUDIT.json`. Hashes are recorded in the result report and issue #4733.

