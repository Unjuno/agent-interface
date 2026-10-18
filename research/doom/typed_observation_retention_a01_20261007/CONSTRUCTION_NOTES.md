# Construction notes

The first packaged candidate invocation stopped before checking any pinned
source because the candidate computed the repository root one directory too
high. It raised `FileNotFoundError` for
`.../new-chat/work/research/doom/map01_overlap_controller_v39.py`. No result
files were produced by that attempt. The package-local root calculation was
corrected, the empty output directory was removed, and the pinned candidate
then completed once as `PASS_TYPED_SIGNAL_RAW_RETENTION_BOUNDARY`.

This was a harness path error, not a controller, telemetry, or live-allocation
result. No source/runtime files were changed. The corrected run's untouched
`RESULT.json`, `events.jsonl`, and `delivered.jsonl` are the retained A01 raw.

The first independent-auditor invocation also stopped before opening the raw:
its package-manifest lookup used `out.parent` rather than `out.parent.parent`.
The path was corrected without changing `RESULT.json` or either stream; the
auditor was then rerun against those same retained bytes.
