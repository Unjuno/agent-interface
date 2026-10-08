# Issue #8592 T0 A03 — bounded DPOR validation

**Disposition: `PASS_DPOR_METHOD_SCOPED`.** The frozen sleep-set DPOR candidate and independent exhaustive auditor each ran once in WSLc and exited 0. Retries: zero. The result is scoped to two finite authored transition systems and supports no live-interface, product-safety, or runtime-speed claim.

## Result

The independent auditor exhaustively enumerated 45,360 complete schedules across the two cases and accepted 217 replayable DPOR representatives after exact comparison of reachable typed outcomes and safety violations:

| Frozen case | Events | Exhaustive schedules | DPOR representatives | Ordered-pair baseline traces | Audited outcome |
|---|---:|---:|---:|---:|---|
| `lifecycle_order_faults` | 7 | 5,040 | 216 | 42 | 8 reachable outcomes; retained `ACK_BEFORE_EFFECT_RECEIPT` witness |
| `commuting_heavy_diagnostics` | 8 | 40,320 | 1 | 56 | 1 reachable outcome |

The commuting-heavy diagnostic control reduced complete schedule enumeration by 40,319/40,320 (99.9975%) and exceeded the frozen 20% schedule-count threshold. The lifecycle case retained 216/5,040 schedules (95.714% fewer). These are schedule counts, not elapsed-time, memory-efficiency, production-workload, or speedup measurements. The auditor checked every declared-independent pair's state/output diamond over reachable prefixes and replayed the candidate's representative and ordered-pair traces. It reconstructed the safety witness `observe:g2 → lease:revoke → task:cancel → tool:dispatch → physical:release → effect:receipt → caller:ack`.

The five frozen auditor rejection controls passed in the separately reported construction suite: omitted schedule trace; underdeclared revoke/dispatch dependence; corrupted typed receipt; erased safety witness; and incomplete ordered-pair baseline. Those are test-suite checks against the exact frozen auditor/test bytes, not extra formal candidate or auditor invocations. The formal audit itself returned `PASS_DPOR_METHOD_SCOPED` with an empty error list.

## Execution and custody

- Allocation: `DPOR-8592-T0-WSLC-CPU-20261008-A03`.
- Final freeze commit: `1d6b13752fda40c0fc61b0a03c6a67666ea1af73`; base main: `948a08d8d0dbea8793edac98f90217a63e752262`. The earlier preformal A03 freeze commit `1f70c3d1e3` is retained in branch history and was superseded before any formal invocation after `git diff --check` exposed CRLF whitespace. Files were normalized to LF, pinned by `.gitattributes`, rehashed, and both construction suites rerun. No result was generated under that superseded freeze.
- Runtime: WSLc 3.0.1.0; Python 3.12.14; linux/amd64; cached `python:3.12-slim`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Both invocations used `--network none --memory=512m --cpus=1`. WSLc warned that swap/cgroup memory-limit capabilities are unavailable; the requested 512 MiB ceiling is therefore not claimed as effective. No model, GUI, user data, GPU, network, or external effect was involved.
- Candidate source was a read-only directory containing exactly five files (four public code/input files and `CANDIDATE_FREEZE.json`); it did not contain `truth.json` or the auditor. The separate audit container received the full frozen package read-only and wrote the audit to an exclusive output path.
- Candidate exit: 0; raw size: 281,943 bytes; SHA-256: `5ad133244809053129cda10360229c0d52bd0d42200e3557bca0343aaf433b59`.
- Auditor exit: 0; audit status: `PASS_DPOR_METHOD_SCOPED`; raw size: 804 bytes; SHA-256: `2b38024c14632dab89201466e3fb2529aaf7d1f498a5850f3ef9e92b67f0a5ca`.
- Construction suite: 20/20 in normal CPython and 20/20 under `python -O`, both in WSLc. `git diff --check` passed for the final frozen package.
- During pre-freeze preparation, the first copied A03 candidate manifest did not match CRLF working-tree bytes. The candidate manifest check caught it before formal execution; the package was normalized to LF, pinned to LF, and both full suites passed again before the final freeze. A subsequent final staged-diff check also passed.
- A01 and A02 stopped before candidate code loaded: A01's single-file mount was unsuitable for WSLc; A02's command used the umbrella folder instead of the Git worktree. Both stops are recorded on Issue #8592, preserved as distinct allocations, and were not retried.

## Reproduction commands

Run from the root of the frozen worktree after checking `FREEZE.json`, the source hashes, current `main`, image identity, branch/commit, and empty output paths:

```powershell
$package = Join-Path (Get-Location) 'research/analysis/bounded_dpor_8592_t0_a03_20261008'
$candidate = Join-Path $package 'candidate-visible'
$results = Join-Path $package 'results'
wslc.exe run --rm --network none --memory=512m --cpus=1 `
  -v "${candidate}:/work:ro" -v "${results}:/out" -w /work `
  python:3.12-slim python run_candidate.py --output /out/candidate_raw.json
wslc.exe run --rm --network none --memory=512m --cpus=1 `
  -v "${package}:/src:ro" -v "${results}:/out" -w /src `
  python:3.12-slim python run_auditor.py `
  --candidate /src/results/candidate_raw.json --output /out/audit.json
```

These commands describe the already-consumed A03 allocation and must not be rerun. The scripts use exclusive file creation.

## Interpretation and limits

This establishes bounded outcome preservation for the frozen, finite model when the declared independence relation is sound over the oracle's reachable prefixes. It does not establish correctness for unmodeled events, repeated identities, fairness/liveness, real time, external actors, UI state, user actions, network/provider behavior, or a running agent. The eight independent diagnostic markers are a reduction-positive synthetic control, not representative production traffic. Exhaustive exploration may remain the simpler choice for small state spaces; a #6206-style ordered-pair suite remains a lower-cost but non-equivalent comparator. No algorithmic novelty is claimed: dynamic partial-order reduction is established prior art ([Flanagan & Godefroid, POPL 2005](https://doi.org/10.1145/1040305.1040315)).
