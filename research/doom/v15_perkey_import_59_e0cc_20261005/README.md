# V15 per-key import identity counterexample

Result: **FAIL_V15_PERKEY_SELECTED_OWNER_IDENTITY** on PR #8065 head `cceb9d2856796cc9b04364806dd67e91610cfabb`. The combined V15 + `--per-key-input-measurement` route selects the raw current V12 owner rather than the archived A01 measurement owner requested by the session code. This package adds evidence only, based on main `7a9398add78d9095e5a85a60d324513fc3c2a1e3`; it does not change either runtime or the implementation author's branch.

## Observed comparison

The exact V12/V15 main functions ran in three fresh Python processes with unchanged repository imports. Optional `vizdoom` and Xlib bindings were inert doubles. The probe stopped at the first `suite.Session()` construction boundary, after backend selection and `sources.json` writing, by replacing that constructor with a recording exception. No session or owner was instantiated. Process spawning, owner-thread startup, X calls and game construction were guarded against execution.

| Route | Selected owner | Selected A01 owner? |
|---|---|---|
| V12 + per-key | archived `dependencies/v12/input_owner_v12.py` | yes |
| Default V15 | current `input_transition_owner_v4.py` | not requested |
| V15 + per-key | current raw `live_control/input_owner_v12.py` | **no** |

The per-key V15 route selects owner SHA-256 `cbfe57373a029aa7d0ae9e70e6cf99806262f8565e27a4415d060bdf73702d9a`, but records the archived A01 hash `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508` from `PERKEY_OWNER`. The V15 manifest also lists current runtime sources; the defect is that recording the requested archive does not bind the selected class to that file, not that every actual owner file is absent from the manifest.

V15 imports the release-batch backend before calling `base.main()`. That loads V4, which imports current `input_owner_v12` into `sys.modules`. V12 subsequently prepends the archived directory, but the bridge's unqualified import gets the cached module. The exact retained import map and owner/class hashes identify this route.

## Consequence and repair boundary

The tested head's raw current V12 `up` branch stores `owner_explicit_keyup` internally and returns `None`. The bridge's `raw()` returns without emitting when it receives `None`, so the promised per-key UP measurement is lost. This consequence is derived from the pinned source contracts; these probes did **not** instantiate an owner or execute an UP. No physical release, timing or task effect was measured.

The existing backend-selection unit test checks an object supplied to the helper, so it does not exercise this session import order. A repair needs an explicit compatible backend/owner binding plus startup and receipt coverage. Simply forcing the historical A01 owner is insufficient to establish current V15 safety: the newly merged release batching and pending-release guards must be preserved. V4 alone also does not establish A01 physical-edge sampling. The original implementation PR remains the repair surface.

## Evidence and first outcomes

- `startup-v5/`: all three collectors reached the intended boundary with exit 0 and no forbidden calls. These exits indicate completed observation, **not** a successful feature gate.
- `startup-v1` through `startup-v4`: retained initial export/import construction failures. First the source exporter chose a same-named `session_v7` from the wrong search path; then package-root, qualified/transitive, and dynamic `real_apps_v1` dependencies were missing. `construction-repair.txt` records each correction. None reached owner/session execution; these failures are harness construction problems, not PR defects.
- `source-manifest.json` and `source-snapshots/`: 56 exact source blobs, stored with `.txt` suffixes so they are inert. Each earlier source manifest is a subset of these immutable bytes. The probe source used by every run is retained beside its receipt.
- `independent-audit/`: a separate agent checked all 56 pins, receipt/log hashes, three result/STDOUT matches, selected/cached identities and the stop boundary without rerunning the startup probe. Its final audit passes. Its first auditor assumption incorrectly equated the default V4 wrapper with its cached underlying raw owner; that check was corrected. The first failing auditor source/output were not retained, and `selfcheck-correction-note.md` states this custody limitation explicitly. The final audit is not represented as the first audit outcome.

Original private raw remains unchanged. Public copies normalize only workspace/runtime path prefixes; `publication-provenance.json` records original/public hashes. Some initial error-log hashes in their receipts therefore refer to the private originals; the publication manifest binds the normalized copies. Final successful stdout/result files need no normalization. Snapshot CRLF bytes remain unchanged.

## Reproduction

With Python 3.12 and the existing Pillow, NumPy and openpyxl dependencies, use a new output directory:

```sh
python research/doom/v15_perkey_import_59_e0cc_20261005/replay_startup.py /new/output/path
python research/doom/v15_perkey_import_59_e0cc_20261005/independent-audit/audit_readback.py /new/audit-result.json
```

The guarded replay wrapper materializes the pinned source snapshots and runs only this startup boundary. It was syntax checked; retained runs used `original-runner.py.txt`. The path-adjusted auditor refuses existing output and was executed on the public artifact copies. That readback is not another startup run. The retained original auditor is inert `.py.txt` because its historical fixed output path could overwrite a result.

H/T/D/C/U were recorded in `PLAN.json` before execution. This was ordinary local construction/regression, not a formal allocation or live-control experiment. No model, game, GUI, X server, container, owner thread, input command, provider timing, release/recovery behavior, threat exposure, application feedback or MAP01 outcome was exercised. No main merge or content-quorum vote is claimed; Issue #59 remains open.
