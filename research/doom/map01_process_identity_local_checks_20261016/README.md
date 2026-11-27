# MAP01 process identity and release-fixture local checks

Retained ordinary regression outputs; no formal/live allocation was executed.
Windows host, Python 3.13.14, python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0,
openpyxl 3.1.5. Fake X clients only. No display, container, game or model launch.

`normal/` and `optimized/` retain every per-module stdout/stderr and summary
from clean source `22633a3171cd72f6cef92ec1e5e1e2ab93de53c5`. The checked-in
`../check_map01_control_regressions.py` ran 33 modules in isolated processes,
with explicit live_control-before-doom import paths. Both modes: 244 methods,
zero failures, one deliberate optional real-Codex handshake skip (243 executed).
The original output directories were fresh and the source status was clean.
Commands used that runner's `--output-dir`, with `--optimized` in the second run.

`repeat-bind-red.log` retains the first supported-repeat-binding regression
failure on `d3dcffdbdc9a83959f1d0133d54159450afebda1` plus the two-line test
addition. After accepted publication, the callback captured a new source and
called the supported binder again. It did not raise; repair rejects repeat
binding before mutation. The frozen runtime at #8949 is a distinct historical
generation-gap characterization and has not been rewritten.

`release-fixtures-base-red.log` retains the isolated four-module baseline check
on a source-only snapshot of exact `067bc1ad7ef2fb226256089c17766a4048428322`.
The two older composition modules fail: 1 failure/1 error and
8 failures/22 subtest errors. The other two modules pass (7 methods).
The first baseline attempt used a sparse checkout and lacked files; an initial
source snapshot omitted real_apps_v1. Both incomplete attempts remain in the
host's consolidation evidence directory and are not the qualified baseline.

Fixture repair implements current batched-UP receipts and explicitly distinguishes
completed release before an error from buffered, never attempted UPs. Existing
malformed key/cancellation/sink mutation/provenance/ledger assertions remain.
The added buffered-UP case requires unknown/unverified evidence. Production
input/release code is unchanged in this fixture follow-up.

These are construction/regression checks, not measured live control results.
No window incarnation, atomic acceptance, physical release bound, task effect,
finite task recovery, or matched efficiency is established. See the
[integration report](../../../docs/maintenance/map01-process-identity-20261016.md).
`MANIFEST.json` hashes retained files; verification does not rerun the experiments.
