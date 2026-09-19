# GTK precheck freeze gate (#2729)

This file is a contract, not an execution result. The gate must fail closed
until every value below is populated from the exact first-result environment.

## Immutable provenance (required before GUI execution)

- `image_reference`: immutable digest or content-addressed build reference
- `image_id`: runtime image ID read from the executed container
- `python_executable`: absolute path and version
- `gtk_version`: exact runtime version
- `xvfb_version`: exact runtime version
- `build_manifest_sha256`: SHA-256 of the build definition/dependency manifest

Mutable tags such as `codex-gtk-model:local` are labels only and do not
satisfy this gate.

## Executable source freeze

Record SHA-256 values for the exact files used by the first run:

- runner source
- fixture source/configuration
- case-definition manifest
- independent scorer
- offline auditor
- dependency/build manifest

The run must emit these hashes into its raw result before any case starts.
The auditor must recompute them from the retained source and reject mismatch.

## Fixed case manifest

Case order is exactly:

1. `useful`
2. `unavailable`
3. `guarded`
4. `no_effect`
5. `partial`
6. `stale_repair`
7. `ambiguous`
8. `cleanup_failure`

Each case definition must specify its operation, expected lifecycle disposition,
authority expectation, replay policy, effect-receipt rule, and cleanup rule.
Names alone are insufficient.

## Gate decision

`PASS_FREEZE_GATE_SCOPED` is allowed only when provenance and all executable
hashes are non-empty, immutable, and independently recomputed before GUI input.
Missing or mutable provenance is `STOP_MISSING_IMMUTABLE_PROVENANCE`.
Any runner/scorer/fixture drift is `STOP_EXECUTABLE_HASH_MISMATCH`.

A freeze-gate pass does not establish effect correctness or formal #2606
acceptance. Those require the separate first-result Docker experiment.
