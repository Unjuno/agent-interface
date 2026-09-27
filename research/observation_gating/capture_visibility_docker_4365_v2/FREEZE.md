# Frozen protocol — successor Docker allocation after #4827 STOP

- Issue: #4835; allocation `capture-visibility-docker-4365-20260927-02`
- Intake main: `f93edb152a68dfbf1098ae1dab9726e9cf90bee4`
- Branch: `research/capture-visibility-docker-4365-20260927-v2`
- Additive path: `research/observation_gating/capture_visibility_docker_4365_v2/`
- #4827's source and failed allocation are immutable; this is not a rerun.

## H/T/D/C/U

**H:** The corrected local Docker/Xvfb fixture collects mapped direct-child `map_state` and geometry without accessing unsupported attributes, completes 12 sessions, yields 4 CLEAR/8 UNKNOWN assessments, and matches an independent pixel/coverage auditor.

**T:** Exact merged #4385 capture adapter and policy, plus corrected standalone runner and raw-only auditor. Six conditions × two fresh authenticated TCP-disabled Xvfb sessions; 640×480×24; parent [43,57,120,80]. Sequence CLEAR, SIBLING_HALF, SIBLING_FULL, CHILD_HALF, CHILD_FULL, RESTORED, repeated once. Preserve both root and window-client capture bytes, metadata, events, geometry, process exits and cleanup. One formal producer run and one separate raw auditor run only; fresh output directory; no retry, replacement, pooling or tuning. Full Docker caps: `--pull=never --network none --read-only --cpus=1 --memory=1g --pids-limit=64`.

**D:** PASS only for 12/12 complete, 24 attempted captures, exactly 4 CLEAR and 8 UNKNOWN, independent raw/geometric audit errors=[], exact source/image identity, and cleanup. Complete contradiction is scoped FAIL; any prerequisite failure is STOP.

**C:** One cached linux/amd64 image, Python 3.11.16, Python-Xlib 0.33, Xvfb. Construction is distinct and excluded. No model, network, user display, input, GPU or runtime authority.

**U:** Docker/Xvfb reproducibility only; no compositor/toolkit/general occlusion, natural rate, runtime or product claim.

## Frozen identities

Image ID `sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0`. Exact local source hashes are in `source_sha256.json`; the adapter/policy Git blob IDs are `2124f531f3b344b6aafed243b2d711baa78b7cbd` / `21bfc2c83d70ef9b69cd214d193705bd4837ecf6`.

Before construction/formal work, publish all source and this freeze on the dedicated branch, read back and verify identical bytes. Then run separate construction confirming child half/full mapped rectangles, restored no-child state, and capture/cleanup. Formal only after these construction gates pass and a fresh output directory is prepared.

No CI/workflow executes the scientific experiment.
