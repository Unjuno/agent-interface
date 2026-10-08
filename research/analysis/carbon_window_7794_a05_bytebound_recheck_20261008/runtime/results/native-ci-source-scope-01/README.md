# Native MCP CI source-scope comparison

The production native-MCP workflow repeatedly spent its5-minute job budget inside
checkout (including PR5612 run36752919239; setup/tests were skipped). The old cone
selection includes research/live_control/results:30,891 committed files totaling
2,825,527,006 bytes at base58b12a314b26a9cee28fa68e15c6b5e8ab2af6cb. This volume is a
plausible contributor, not proof that every cancellation has that cause.

A fixed-commit local pair compared the exact old cone selection with non-cone
patterns selecting the runtime packages and files directly under research/live_control.
Nested research bundles are omitted from this contract-test job. All top-level
research modules/requirements/source-gate inputs remain selected; a future nested
fixture dependency must be added explicitly. Historical data stays in Git.
The workflow timeout, dependency installation,47 Node checks and fixed Python suite
commands are unchanged. [actions/checkout v4 documents non-cone selection](https://github.com/actions/checkout/blob/v4/README.md#fetch-only-a-single-file);
its [source](https://github.com/actions/checkout/blob/v4/src/git-source-provider.ts)
uses blob:none for sparse fetch and then checks out selected blobs.

One matched pair on WSL3.0.1/Ubuntu, kernel6.18.40.1, Python3.12.3, Node24.13.1,
Git2.43.0. CI uses Node22, so this is not identical to the hosted runner image.
Both local selections passed47 Node tests (zero skips),324 protocol tests and141
harness tests. Native runner bytes and Node commands are unchanged across routes.
Every candidate materialized file is the same path/size/hash as its baseline member.

Materialized tracked files: baseline35,718 /2,864,509,379 bytes; candidate2,089 /
10,115,800 bytes. Reduction99.6468575% of tracked-file bytes. Manifests retain every
path, size and SHA256. This does not count Git object storage, network packets,
working-tree metadata, dependency installation or generated test files. Local
worktrees share the existing Git object database; fixed order/cache effects and
single-pair timing preclude a network-speed or remote-stability claim. Recorded
command timings are diagnostic only, not GUI latency or human-tempo measurements.

The first local shared-clone setup failed exit128 while serving a promised object
from the partial repository. Its exact receipt/stderr and runner are retained as
STOP_SETUP, not a test failure, comparison route, or corruption diagnosis. The
completed pair instead used two independent worktrees at the fixed commit. After
capturing results, their source copies were removed through Git after checking
resolved paths, zero tracked changes and only generated pyc files; actual cleanup
receipts are retained. Original source and frozen allocations were not removed.

Integration: Native MCP workflow now uses the tested non-cone patterns. No runtime
behavior, test selection, timeout extension, GUI replay, model substitution, sensor
or automatic fallback was added. The shared integration guide records dependency
maintenance and the difference between local tests and remote validation.

The62-file archive contains the plan, both tracked-file inventories, command
receipts, Node/full Python logs, setup failure, cleanup/environment, old/final
workflow and exact shared runner bytes. `python -O runtime/results/native-ci-source-scope-01/verify.py`
checks archive closure, subset byte parity, unchanged workflow commands and selected
result invariants; it performs no checkout, tests, network transfer or adoption audit.
Remote CI outcomes are recorded separately on the integration PR. This is an
integration-cycle improvement, not product completion, token saving or operation speed.
