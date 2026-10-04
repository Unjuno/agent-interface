# Batch release cancellation composition A01

This one-shot Fake-Xlib construction composes current-main `input_owner_v12.py` (main `dae347cb83`) with the per-key batch-release interval instrumentation from #7504. It tests the narrow interval where cancellation becomes set inside the batch-release XSync callback. The candidate records `reason=cancelled`, a verified empty state, one interval per released key and only one batch XSync. An adjacent explicit-up case confirms the current-main post-sync cancellation receipt remains intact.

This race is distinct from the currently open #7529/#7533 telemetry checks: their batch case sets cancellation before automatic cleanup begins, while their explicit-up case injects cancellation during the per-key up sync. A01 injects cancellation during XSync for an already-requested ordinary batch `release`, where the release reason began as `release` and must be reclassified after sync.

The PR also tightens two unrelated CI path filters that matched every nested `research/live_control/**` result bundle even though their sparse checkouts consume only top-level live-control files or a fixed source list. `native-mcp-v1.yml` now uses the top-level-only `research/live_control/*`, limits push checks to `main`, and skips its workflow-file-only push because the PR event already checks that edit. `full-golden-ipc-source-integrity-2737.yml` names its result, auditor and four pinned live-control source files. Its workflow-file edit still receives one PR check.

The candidate ran once on macOS 27.0.1 arm64 / CPython 3.14.5 after the local OrbStack content store failed both image inventory and fresh-image pull with `operation not supported`. This result is explicitly host-synthetic; no container run occurred. See `ORBStack_SETUP_STOP.json`, `FREEZE.json`, `SOURCE_MANIFEST.json`, `RUN.json` and `raw/trace.json` for exact provenance.

The first frozen auditor returned `FAIL_AUDIT` because it expected a different raw schema label than the runner emitted. That original output and exit receipt are retained. The candidate and raw were not changed or rerun. Read-only audit v2 corrected only the schema expectation; its mutation controls rejected a wrong schema, an interval extending past verification and a missing explicit-up cancel marker. The repaired audit returned `PASS_SYNTHETIC_COMPOSITION` with zero errors.

The intervals are synthetic request-start-to-one-sync-return bounds. This does not establish physical key-up timing, real X11 delivery, task effect, useful feedback, bounded recovery, safety, speed or a live #59 result. The #59 live allocation remains unassigned and open.

Read-only re-audit of the retained result from this directory:

```sh
python3 -B tests/test_audit_a01_v2_mutations.py
python3 -B audit_a01_v2.py
```

### Additive V3 trace-custody check

The V2 audit above is retained unchanged. Its review found that semantically unscored fields in `raw/trace.json` could be edited without affecting V2's PASS. V3 therefore verifies the raw file's exact bytes against the pinned `raw_trace_sha256` before parsing it, then delegates the unchanged semantic checks to V2. `tests/test_audit_a01_v3_trace_hash.py` demonstrates the gap (V2 accepts edits to `started_at` and the batch `owner_id`) and confirms V3 rejects the altered bytes before parsing. Run:

```sh
python3 -B tests/test_audit_a01_v2_mutations.py
python3 -B tests/test_audit_a01_v3_trace_hash.py
python3 -B audit_a01_v3.py
```

This is a read-only audit successor; the candidate, original raw trace, first failed audit, and V2 freeze remain unchanged. No candidate or native/X11 experiment was rerun.

The candidate allocation is consumed and must not be run again under A01. A future candidate execution requires a new allocation ID and an explicit delta. The first auditor is intentionally retained as the original failed version; the final command uses the versioned read-only repair and does not rerun the candidate.
