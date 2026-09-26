# Result — Issue #3903

Status: `PENDING_FROZEN_FORMAL_RUN`.

## Decision

`PASS_STATIC_IMPORT_BOUNDARY_SCOPED` — exactly one Docker Desktop formal invocation; independent audit `AUDIT_PASS`, errors `[]`; eight controls passed. Zero target imports, target executions, game starts, model calls, or input events.

## Finding

The exact pinned `session_entry.py` has an unguarded module-level `session_map01_v13.main()` call at line 18. A conventional import of this file would immediately invoke the archived session entrypoint; therefore #3857's `STOP_FORBIDDEN_LAUNCHER_SIDE_EFFECT` is supported for the actual target, and no import-safety claim is warranted. The same frozen controls also demonstrate the old gate's whole-AST `main` scan over-flags `main()` calls confined to a deferred function or lambda body; the narrower AST classifier correctly treats those as deferred while counting decorators, defaults, class bodies, and unrecognized conditional module code as import-time execution.

This was a static source audit only. The launcher and all transitive dependencies stayed unimported and unexecuted. No workflow, game, model, GUI, input, or runtime behavior was tested.

## Provenance and retained outputs

- Frozen issue #3903 branch HEAD: `076a6f6581992312e3925125501e67046f42fd6e`; source snapshot: `8652f6a3527d55610185d1103b87d5d9fd8fa985`; exact six-source SHA-256 manifest is in the [freeze comment](https://github.com/Unjuno/agent-interface/issues/3903#issuecomment-5753096696).
- Docker Desktop 28.5.1, `desktop-linux`, image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, Linux/amd64; no pull, no network, read-only root/source, separate writable result mount.
- `formal_result.json` SHA-256: `b6ee63aa4c6abd40a82dd6df98babe051068312422da879cdbdeb6dbd20ad4bf`.
- `independent_audit.json` SHA-256: `15e48cb95e28ebc03bff95bae455ca163e7eec68eec08fb9fdc53c0b59188174`.
- `RESULT.json` SHA-256: `de581c3a89ed7b1705be6c4101c39aaec6c56a92eed331befde7654698d22e11`.
- `construction-01/CONSTRUCTION.json` SHA-256: `b56fac6fed9313a47de049b5a43f0cca890a195cdd2b870c8a04d296eec22dc3`.
- `construction-02/CONSTRUCTION.json` SHA-256: `05fad5f97793274d3f228b5e1f09cf6326cf3c4ff0147fb131fa9581bbc268b8`.
- Two early command-construction STOPs on the collided predecessor branch remain documented in [PLAN.md](PLAN.md); they occurred before target access and were not formal attempts.

## Limits

This confirms only the source-level import boundary and this AST classifier's frozen controls. It does not prove imported dependencies safe, workflow correctness, archived experiment validity, gameplay, model behavior, or any runtime/product property.

Do not infer import safety, runtime behavior, workflow validity, or gameplay from the pending audit. Update this file only after the one formally frozen container invocation and independent verification.
