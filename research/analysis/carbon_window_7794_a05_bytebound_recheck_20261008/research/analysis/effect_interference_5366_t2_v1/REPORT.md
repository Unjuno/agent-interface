# Issue #5366 T2 — semantic effects vs resource interference

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite synthetic contract fixture. Candidate and independent auditor each ran once, both exited 0, and retries were 0. The auditor independently reconstructed all 15 policy/case rows with `errors=[]`. Construction suite: 5/5, including rejection of five corrupted-raw mutations.

This is not evidence of actual X11/AT-SPI cost, timing, workload incidence, runtime safety, task effect, or product benefit. It does not prove that a declared resource bound is sound or portable.

## H/T/D/C/U

- **H:** A semantic-only `read(ui)` row can allow resource interference that makes an unrelated controller miss its response deadline. Keeping resource interference as a second effect dimension can preserve known-benign reads while refusing over-budget and unknown envelopes.
- **T:** Five synthetic observations share one serialized server. Each read begins at `t=-1 ms`; a controller arrives at `t=0`, needs 1 ms service, and has a 2 ms deadline. Three policies are compared: semantic-only, reject-all, and semantic-plus-resource. The resource policy receives only the declared bound; latent service time is reserved for scoring.
- **D:** The frozen gate required 15/15 exact reconstruction; fast/cache-hit admitted; slow/cache-miss refused; unknown remained non-authoritative; no late controller under the resource policy; semantic effect remained `read(ui)`; five mutation controls rejected.
- **C:** A real scheduler/serializer may dominate a static resource manifest; blanket refusal could be appropriate under a stricter contract; declared bounds may age under changed load.
- **U:** Values and queue are hand-authored and deterministic. There is no real UI, observer, runtime, model, network, GPU, task, or authority path. A synthetic method PASS does not validate any live timing bound or production policy.

## Result

| Policy | Admitted | Controller deadline misses |
|---|---:|---:|
| Semantic-only | 5/5 | 3/5 |
| Reject-all observations | 0/5 | 0/5 |
| Semantic + resource envelope | 2/5 | 0/5 |

The two-dimensional gate admitted `fast-read` and `cache-hit`, denied `slow-read` and `cache-miss` because their frozen worst-case completion exceeded 2 ms, and returned `UNKNOWN_RESOURCE_ENVELOPE` for `unknown-envelope`. The blanket policy demonstrates the availability cost: it also rejected both known-benign reads. No dimension relabeled resource occupancy as an external write or authority effect.

## Frozen source and formal execution

- Main base: `c69fa71501a0e42abc3ffe435ae72949d5d15877`.
- Source/input hashes: `FREEZE.json` (candidate, auditor, fixture, plan and construction tests were hashed before the formal run).
- Candidate command, once: `python3 candidate.py fixture.json outputs/formal/candidate_raw.json` — exit 0, 15 rows.
- Independent raw-only audit command, once: `python3 audit.py fixture.json outputs/formal/candidate_raw.json outputs/formal/audit.json` — exit 0, `PASS_METHOD_SCOPED`, 15 rows, zero errors.
- Candidate raw SHA-256: `d452bcad1404bdf6f08b164f010f634129ab30ce7329237baed4c1191181a567`.
- Audit SHA-256: `2c9e52e4517540519fa46c34683bdc9a80ff5b3514fc24036998ae430a10ef65`.
- Freeze SHA-256: `891b9ef21639a06903684d5fa8ddc57031df2cb134f1635bf198df427a79ecc8`.
- Runtime: CPython 3.14.5, macOS arm64, standard library. No container started. OrbStack was responsive, but an owner-unknown shared container remained active and Issue #5085 did not grant a second launch; no existing container was inspected beyond its name/status, stopped, or modified.

The first construction-test invocation from repository root failed with `ModuleNotFoundError` because the test expects its own directory on the import path. It occurred before any candidate invocation. The corrected package-directory command passed 5/5; both events are preserved in `CONSTRUCTION_LOG.md`. No formal output was retried or edited.
