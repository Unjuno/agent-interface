# Generation-bound evidence provenance successor #2196

Status: PASS_CONTAINER_PROVENANCE_COMPLETE_SCOPED only after the workflow artifact is independently checked.

This additive successor preserves the exact #2166 harness source while requiring the workflow to retain the parent Git blob identity, runtime source hash, resolved container image digest, exact stdout, and result SHA-256. It does not claim X11/PNG capture, model value, task input, latency, or runtime transfer.

The workflow performs one fresh container execution and uploads the provenance bundle.
