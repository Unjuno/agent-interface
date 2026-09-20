# Float32-aware invalid-control audit (#3906)

Audit-only successor to #3899. The immutable predecessor auditor reconstructs the complete result; this layer checks all invalid-control identities exactly and their finite float32 features within a frozen `1e-6` tolerance, then normalizes only an in-memory copy for the predecessor's decimal-literal comparator. Raw result bytes are independently SHA/blob-bound and never changed.

See [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and [FREEZE.json](FREEZE.json) for exact identities and one-shot local Docker command. No training, inference runner, GPU, network, or retries.
