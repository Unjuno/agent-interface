# Issue #6610 T0 result (2026-10-02)

Disposition: METHOD_PASS_SCOPED.

The frozen finite synthetic assay covered 6 cases across spreadsheet and drawing fixtures, with no-follow-up, structural-edit, and raster-patch strata. A separate WSLc invocation of the independent raw-only auditor reported 35 checks, 5/5 corruption controls rejected, and no errors. The initial-only ranking favored flat (1 vs 3 declared operation units in each family); under the declared 0.4/0.4/0.2 follow-up mixture, structured favored (spreadsheet 4.2 vs 4.8; drawing 4.2 vs 4.4). No-follow-up and raster-patch strata favored flat.

The exact candidate raw JSON remains in the local companion results directory and is identified by SHA-256 E9D2678D08358A59F4160FF9701AAF05C93F60F06F55429D0017D875D4E9062F. Auditor JSON SHA-256: 1DD7C32D81DC927FD9C70AFE02695EE8F00AAEB81D754C41FDB6BEBD0CA3926C. The full raw JSON is not duplicated here because the GitHub connector's blob transfer normalized/truncated an oversized base64 payload; the result and hashes are recorded without representing that transfer as exact.

Execution: pinned local python:3.12-slim image, ID sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4; WSLc, network none, read-only source mount, separate candidate and auditor containers. Both invocations emitted a kernel warning that swap limits/cgroup were unavailable; memory-limiting behavior is therefore not independently verified. Candidate and auditor commands each exited 0. One auditor launch failed before execution due to invalid image-reference syntax; the corrected auditor invocation succeeded. Candidate was not rerun.

Scope: finite hand-authored synthetic method-sensitivity test only. Integer operation-cost units are not time or real effort. The mix is illustrative, not user-derived. No claim about real applications, editability, preferences, model behavior, or product benefit.