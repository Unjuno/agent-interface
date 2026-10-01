# Allocation 07 source recovery and construction recheck

**Disposition: source recovered; supplemental construction reproduced; formal allocation remains NOT STARTED (0/18).** This archival/recheck record does not promote the allocation or authorize its formal run.

## H/T/D/C/U

- **H:** In one stable producer generation, an explicitly declared bounded sequence counter can wrap from 255 to 0 at modulus 256 without implying a generation reset. Timestamp-only acceptance admits gaps; strict linear ordering rejects a valid wrap. Missing modulus must be `UNKNOWN_COUNTER`.
- **T:** Preserve the original allocation-07 freeze and compressed five-file source bundle unchanged. Independently verify its five source hashes, run its five policy unit tests, then run only `run.py --mode construction` (one row for each of six scenarios) in CPython 3.13.5 on Linux x86_64. Do not invoke `--mode formal`.
- **D:** Construction recheck passes only for 6/6 child exits zero, candidate outputs matching the frozen six-scenario outcomes, `audit.py` errors empty, and all eight corruption controls rejected. This is a construction gate only.
- **C:** Synthetic producer subprocesses over stdout pipes; single producer generation per case; explicit modulus 256 except the missing-modulus control; 20 ms threshold. The container uses Debian 12 on OrbStack's Linux 7.0.14 kernel; it does not reproduce the historical kernel string exactly.
- **U:** No formal 18-row allocation, X11 or independent application event stream, dropped transport, multiple producers, hostile/reused generation IDs, cross-host clock, GUI/model/task benefit, runtime promotion, or reliability claim is tested here.

## Execution record

The immutable `SOURCE_BUNDLE.gz` SHA-256 is `10e44d5d60de7b7cb26bb0703f9aa210ea99f34128463a40a6971d091dc08d44`. Its five expanded source hashes matched `SOURCE_BUNDLE_META.json` in the x86_64 container.

The successful x86_64 run used image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (`python:3.13.5-slim`), `--platform linux/amd64`, and `--network none`. Results are under [`rechecks/construction_20261001_04/`](rechecks/construction_20261001_04/):

- `python -B -m unittest -v test_policy`: **5/5 passed**.
- `python -B run.py --mode construction`: **6/6**, all exits zero; candidate `SATISFIED=3`, `EXPIRED=1`, `UNKNOWN_GAP=1`, `UNKNOWN_COUNTER=1`; all six matched expected outcomes.
- `python -B audit.py RAW.json --controls`: `errors=[]`; **8/8** corruption controls rejected.
- `RAW.json` SHA-256: `4063de7b511350cc35d04d2998c09c9d13b8d5299ff31145b8e8b92a7bd06b67`.
- `SUMMARY.json` SHA-256: `907ec45a8c20ba0637b74becaada9dbb9457ebd23f3d14133cd96765aff4368c`.
- `AUDIT.json` SHA-256: `6bc3c1a4c162e40fea0a8a3415d75c7e042ae9fe763d955766675d8147226a07`.

A separate successful `linux/arm64` container run is retained at [`rechecks/construction_20261001_02/`](rechecks/construction_20261001_02/). It produced the same unit/construction/audit counts; its RAW SHA-256 is `b38d85a8ab45c662911929454669cd1fd2e3f22fa639946515f6d40a7f937321`. This is supplemental, not a substitute for x86_64.

Two harness invocations stopped before the producer was called and produced **zero scientific rows**: (1) the initial output bind mount itself existed, so `out.mkdir(exist_ok=False)` raised `FileExistsError`; (2) a later x86_64 attempt had its named output child pre-created, causing the same pre-run error. Exact stop classifications are in [`rechecks/SETUP_STOPS.json`](rechecks/SETUP_STOPS.json). No partial RAW was accepted from either. The successful x86_64 run changed output transport: the container generated into its private temporary filesystem, then returned the completed evidence as a tar stream.

## Local integration checks

- `git diff --check`: PASS.
- `python -B -m unittest discover -s research -p 'test_*workspace*.py' -v`: **21/21 PASS**.
- `python research/check_workspace_index.py --git-tree`: PASS; **152** top-level research directories indexed.
- `python -B research/analysis/check_index.py`: PASS; **306** retained result/failure directories indexed. Advisory only because this addition is outside `research/analysis/`.
- Native MCP CI's exact Node test list in Node **22.23.3**: **109/109 PASS**. One initial Node-only container lacked `python3` (107 passed, two `ENOENT`); installing the CI helper interpreter in the disposable container resolved it.
- `python runtime/integration_checks/native.py --output /tmp/native-ci` in Python **3.12.14**, with the workflow dependencies and Git: **156/156 PASS**, both `protocol` and `harness` suites. The first minimal image lacked Git (9 environment errors); the next attempt used global `GIT_DIR` variables, which leaked into two tests creating temporary repos. The passing run instead mounted this linked worktree's Git metadata read-only at the absolute location named by `.git`, without Git environment overrides. No repository source was changed by these local CI runs.

An earlier invocation with unsupported `--git-tree` on the analysis-index script returned its usage error without running the check; the workflow's exact command was then run successfully. All check commands above were rerun successfully under the applicable workflow invocation.

## Boundary and next gate

The source's `FREEZE.json` remains unchanged: allocation `app-sequence-wrap-2802-20260923-01`, `formal_invocations=0`, `formal_rows=18`, `formal_state=NOT_STARTED`, `reruns=0`, `replacements=0`, and `tuning=0`. Construction evidence does not satisfy the plan's formal 18-row gate. Keep the Issue open and require an explicit owner/resource disposition plus the frozen formal environment/gates before any formal command. This result supports archival publication only.
