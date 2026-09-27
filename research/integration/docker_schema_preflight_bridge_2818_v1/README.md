# Docker schema-preflight bridge (#2818)

This additive, no-GUI bridge validates the existing shared-volume Docker to
host-model IPC boundary before any task or input authority is acquired. It
accepts only a matching request id, one completed turn, one completed message,
and explicit `authority_granted: false` broker/runner receipts. Missing,
malformed, timeout, nonzero-return, or mismatched responses fail closed.

The bridge is a contract gate, not a model-quality, GUI-effect, latency, or
six-task result.

