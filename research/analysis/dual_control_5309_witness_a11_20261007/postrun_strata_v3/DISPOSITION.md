# V3 disposition

**`STOP_WRAPPER_EXIT_STATUS_CAPTURE_FAILED`**

The one-shot V3 program wrote a complete retained-data reconstruction payload: 264/264 rows, zero reported errors, zero unsupported completions, corrected descriptive strata, and explicit separation of V3 diagnostic allocation from the A11 source allocation. The output file and captured stdout are byte-identical.

The enclosing zsh command then failed with `zsh:1: read-only variable: status` while attempting to preserve the just-finished process status. The wrapper exit was 1; the V3 program's own exit status is unknown. The prespecified stop rule does not permit calling this allocation PASS with that process-level evidence missing. The output verdict remains exactly as emitted and is not edited to match this disposition.

No retry is permitted. This STOP does not alter or qualify the formal A11 result `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE`; it is a diagnostic execution-wrapper STOP only. V2's questionable provenance remains unresolved by V3, whose output is retained as a distinct successor observation rather than a repair of V2.
