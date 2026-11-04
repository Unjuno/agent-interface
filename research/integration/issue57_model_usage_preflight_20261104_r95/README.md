# R95 — preserve same-API file-change detection

## Finding and correction

After PR #10207 enabled `st_birthtime_ns` where available, ASTORA's read-only review found that `_identity()` also fed comparisons within the same stat API. On platforms that expose birthtime, a change to ctime during the read could then be hidden when size, mtime, and birthtime stayed fixed. The Windows cross-API mismatch was fixed, but this weakened the same-API mutation guard.

`calc_effect_v1.py` now compares stable identity across `lstat`/`fstat`, while `_same_stat_version()` additionally requires equal ctime when comparing the two `fstat` samples and the two `lstat` samples. Regression tests simulate ctime-only changes separately for the descriptor and path samples while preserving birthtime and all other identity fields.

## Verification

Base source tree: main `9970ff445cfcd67d5c00c1db41f7aa47a65689f5` (the merge of #10207) plus this two-file patch.

- Windows Python 3.13: Calc effect/artifact suites 25/25 PASS, normal and `-O`.
- Windows Python 3.13: Fake App Server → public MCP → Calc composed test PASS, normal and `-O`.
- Docker Engine 29.8.1, image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, Linux/amd64, network disabled, read-only source, 2 CPUs, 4 GiB RAM/swap, 256 PIDs: the same 25-test suites pass normal and `-O`; the composed test passes normal and `-O`; container exit 0.
- `git diff --check`: PASS.

The packet retains both Docker outputs. The first run failed because the new Linux test fixture supplied `None` for birthtime on a platform without that field, so it did not hold birthtime constant as intended. The fixture now supplies a stable simulated birthtime; no runtime failure remained on corrected rerun. Windows console stdout is retained in the active local tool record.

## Scope

This is a filesystem identity/mutation-detection regression and offline Calc composition. No live model call, WSLc allocation, GUI input, task-economics trial, or MAP01 run occurred. The integrated live comparison remains unresolved.
