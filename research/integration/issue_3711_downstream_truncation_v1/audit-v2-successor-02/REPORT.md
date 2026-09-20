# Corrected artifact audit — successor 02

Disposition: `PASS_V2_ARTIFACT_BINDING`, zero errors. This is a post-run, read-only audit; the CLI experiment was not rerun.

The audit ran in a fresh OrbStack Docker 29.4.0 container (`linux/arm64`) using the pinned Python 3.12 image, with `--network none`, source and formal-02 evidence mounted read-only, and a separate output mount. It independently confirmed:

- The formal allocation source base is `2dff80852292cc82fd5c23a449c8244bea94bc25`; the later audit-code base is `e6f74d3b9fef0467327823ab97cb15f0dbe59ac4`. They are distinct and correctly bound.
- The v2-01 audit failure is unchanged and contains only `ALLOCATION_OR_BASE_MISMATCH`.
- Actual `formal-02/attempt/request.json` and `attempt/report.json` exactly match the published copies and actual `attempt-status` stdout values/hashes.
- The recursive attempt-directory snapshot exactly matches both pre- and post-recovery snapshots in raw evidence.
- Full accepted output parses as JSON; the 23-byte delivered prefix is rejected with `JSONDecodeError`; producer's full acceptance count and dispatch-once record match.
- The original formal freeze, all frozen source hashes, raw result, and v1 audit hashes match their pinned values.

No dispatch/backend or GUI was invoked. The failed audit v2-01 result and original audit v1 output remain untouched; this successor does not retroactively rewrite either disposition.
