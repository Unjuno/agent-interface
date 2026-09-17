# Source-first freeze

Task: `X11-GIL-SWITCH-TARGET-CUE-20260916-002` / Issue #462.
Publication base: `76d9623962fc6c8136cce30450d641751e73eb39`.
Formal rows executed at freeze: **0**.

Only setup acquisition differs from stopped #457: Xvfb uses fixed private display `:462` after an explicit socket-absence check. Scientific mechanism remains 12 matched target pairs, 5 ms cue, 2 ms watcher cadence, 600 ms authority deadline, target threshold 512, same-interpreter competitor, and 5 ms vs 1 ms CPython switch interval.

Construction executed no live target/nuisance cases; only build, Xvfb readiness, exact ROI-count boundary and invalid-argument guards.

## Frozen SHA-256

- `audit.py`: `f2ecdf2ca7042562f064efc7c037ee5dfe4c16e6222ab2d5f2f1384688bcb511`
- `build.py`: `d8ccef266858b32acb54cc11f2f1877dca698b2f26d4bc3d619d5d1c8a818962`
- `native_acquire.c`: `682742c79ee86f50e1052826bdb7754c80013a9f38c7cc400a26219dd7db7751`
- `native_predicate.c`: `ff69a2281b1081be80cb0051517c4eb5ce1ea13092f3baf0934bb01630d7528c`
- `run.py`: `01082fcdbdf45ab6c74fc0a42b07d68ff71f00e0109e17505ee4c34a121d0cf0`
- `test_audit.py`: `8dd7616d88bd066ae476b2c7a6ea14580415ab406ca57062818bc10d1f6c26e8`
- `upstream_poll.py`: `d50233d9584876f119e78251728ccbf682a4b46b5485197ae60229970d9d520d`
- `native_acquire.so`: `981d27e9efa67443206527cc68ec6cfa3295889c319abbd9054cdac7f8817ddb`
- `native_predicate.cpython-313-x86_64-linux-gnu.so`: `fb091f2997882c664e740d90c8f5f1c8a8f64d86410ede851a08105aa01e1d3d`
- `prereg.json`: `0bbc300287c0fe8407ec82c9bb9b4a34c395d303d93a5a2ef2f6596a112b946b`
- `environment.json`: `e05fc7e217a585ad6dae5cf15dfc10e94f020ab8cae0a4fb934587ddaf1fec2d`
- `SOURCE_DELTA.patch`: `705bf18f46bdd463e6efeb071c41eab7cc740089ff85561b8b6dd59511291cf2`

Stopping rule: one formal block only; no retry, replacement, extension or post-data threshold tuning.
