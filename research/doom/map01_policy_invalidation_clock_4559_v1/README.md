# MAP01 running-action clock diagnostic adapter v13

This additive adapter wraps the frozen v12 candidate without editing the shared controller or guard modules. It records the exact runtime decision value, snapshot sequence/capture time, signed comparison delta, same-call host timestamp and lower clock offset, clock-domain labels, source event capture/typed-ready/emit values, and the current same-session calibration stage/probes with a canonical SHA-256 identity before `check_current`. The JSONL record is flushed before the guard call and fsynced on an inverted-time boundary; a logging failure therefore stops before the guard, preserving fail-closed behavior.

## Local construction evidence

- Base: `main` at `342d11c09e8cb8fe5cf8677d285b5ef616050539`.
- Unchanged source blobs: v39 controller `321ec02e5c3c8bd87c6370e4a5e90bb3013d4241`; predecessor v12 adapter `cba1fd6d7d371941d15e9f15d870721497c78474`.
- Adapter SHA-256: `57517bf2f9c57cfac5e8686951bc261c4bb1c4264590e4ca68094ec9a89aa0a3`.
- Effective source SHA-256: `5ba55ce2007b6214438618ac32ceb9b49b6bc63c522ff7a17912b883b68250d5`.
- Runtime image: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, linux/arm64; WAD SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- PASS: effective source generated and parsed; pinned-container syntax/guard-anchor check; mocked inverted-boundary record persisted before the original exception; logging failure stopped before guard invocation; `git diff --check`.
- Container JSONL/fsync round-trip PASS (record SHA-256 `b1750b0bbd8683bacc85792e73ee42f9b8bc6c8cc7cfeac16bcd5bf00781bd8f`).
- Mock-only logging overhead sample: 500 instrumented checks median 48,166 ns, p95 96,542 ns, max 283,958 ns; 1,000 no-log checks median 4,541 ns, p95 4,709 ns, max 64,500 ns. This is not gameplay/runtime performance evidence.
- One exploratory container command encoded a literal backslash-n and failed JSONL parsing; corrected command passed. Two mock preparations had invalid test fixture/import assumptions; neither invoked the formal seed. Do not count these as semantic failures.

No Obstac-specific MCP, executable, or local configuration was available in this environment at inspection time; the container checks used Docker/OrbStack. Preflight seed `990643` has been consumed; its first allocated output path retains an initialization failure, and the successful retry is recorded below. Formal seed `990642` remains unused pending final worker collision/ownership confirmation and exact provenance update in Issue #4563.

## 2026-09-27 experiment update

Preflight seed `990643` has now been consumed by a zero-model Docker MAP01 observe/release run, and a controlled real-observation timestamp-boundary replay has passed. These scoped results do not reproduce the natural #4544 inversion or clear the formal-seed gate. Full hypotheses, controls, uncertainty, commands, evidence hashes, and retained output paths are in [EXPERIMENT_20260927.md](EXPERIMENT_20260927.md).
