# Issue #5366 T3 — resource-envelope freshness

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite synthetic load-generation fixture. Candidate and independent raw-only auditor each ran exactly once, both exited 0, retries=0. The auditor reconstructed all 12 rows with `errors=[]`. Construction suite: 5/5, including four corrupted-raw controls.

This does not measure real resource load, X11/AT-SPI service time, generation tracking, runtime safety, task effect, or product benefit.

## H/T/D/C/U

- **H:** A resource bound learned under a prior load generation can admit a read that misses the controller deadline after shared-resource load changes. Binding the envelope to the current generation should fail closed as UNKNOWN while preserving current under-budget work.
- **T:** Four synthetic observations on one serialized server; read begins at t=-1 ms, controller arrives at t=0, requires 1 ms, and has deadline 2 ms. Compare semantic-only, declared-bound-only, and generation-bound resource policies.
- **D:** All 12 rows must reconstruct; current-low admitted; stale bound UNKNOWN/non-admitted; current over-budget denied; missing bound UNKNOWN; freshness-aware deadline misses zero; semantic/resource dimensions remain distinct; four mutations rejected.
- **C:** Fresh measurement, scheduler serialization, or blanket refusal may be safer or simpler than versioned manifests. Invalidating on every load change can sacrifice availability.
- **U:** Service times and load generations are hand-authored. This is a method-only finite model with no actual GUI, runtime, model, network, GPU, host input, or authority path.

## Results

| Policy | Admitted | Controller deadline misses |
|---|---:|---:|
| Semantic-only | 4/4 | 2/4 |
| Declared resource bound, no freshness check | 2/4 | 1/4 |
| Generation-bound resource envelope | 1/4 | 0/4 |

Without freshness binding, the old `g1` 1 ms envelope admitted the `stale-low` case after the fixture changed to `g2`; its actual 4 ms occupancy made controller completion late. The generation-bound policy returned `UNKNOWN_STALE_RESOURCE_ENVELOPE`, admitted only `current-low`, refused `current-overbudget`, and left `current-unknown` as `UNKNOWN_RESOURCE_ENVELOPE`.

## Execution and provenance

- Main base: `5863696c67338d380820faa4ba1a866e0d25719b`; full H/T/D/C/U and base refresh were posted before formal execution.
- Candidate: `python3 candidate.py fixture.json outputs/formal/candidate_raw.json` — 1/1, exit 0. Raw SHA-256: `b93ec4f2635920eded3758325fed095cb2e4980937e94795b4609cfde9a929ed`.
- Auditor: `python3 audit.py fixture.json outputs/formal/candidate_raw.json outputs/formal/audit.json` — 1/1, exit 0, 12/12 rows, zero errors. Audit SHA-256: `129f5add800c68904770bdeabc58536f7587b3bb930029688c91d14412bd7a94`.
- Freeze SHA-256: `44c44cb3bcfc17c9a70f3a4e942d5d7bf61f08ba12ccdb6a78e55db6e42b175d`.
- Runtime: CPython 3.14.5, macOS arm64. OrbStack was not used: the owner-unknown shared container noted in #5085 was left untouched, and the synthetic workload has no Engine-specific behavior.
- Local CI equivalents after rebasing the PR branch to main `93f0ee168051d4b4afcf381ea8e88245d89448f5`: analysis index 376/376; construction 5/5; analysis workflow suites 8/8 and 12/12; workspace-index tests 21/21 and index 154 directories; public navigation 26 documents / 1,233 links; Python compilation and diff check pass. Hosted workflow results are not claimed.

The #5366 T2 record and all earlier issue results are unchanged. This successor demonstrates why a resource envelope needs currentness/provenance; it does not validate how a live system measures or invalidates that envelope.
