# Issue #7794 comparator semantics diagnostic A04 — PASS_DIAGNOSTIC_SCOPED

The one-shot candidate and independent auditor both exited 0. The auditor reconstructed all 10 rows: all nine frozen A02 cases had equal global-lexicographic and canonical serial-ASAP schedules; the fixed two-job discriminator differed. Global enumeration returned A=1, B=0; serial ASAP placed A at 0 and could not fit B before its deadline. This supports that the comparator definitions differ and that the retained nine-case A02 fixture does not distinguish them.

The result is finite synthetic comparator semantics only. It does not challenge A02's separate schedule-cost audit and does not establish a carbon benefit, operational scheduler behavior, realistic workload effect, energy, emissions, or runtime performance. The A03 output-path STOP remains immutable and was not retried.

## Environment and disposition

OrbStack image inspect, image listing, and pull failed with containerd blob `operation not supported`; no alternate container runtime/context was available. This is a disclosed native macOS 27.0.1 arm64, Python 3.14.5 standard-library CPU-only fallback, not a container PASS. No shared daemon repair/prune/restart was attempted.

Candidate invocations: 1. Auditor invocations: 1. Retries: 0. Exit codes: 0/0. Both stderr files are empty. The preregistered output directory existed before either formal invocation.

## Verification

- Frozen input and candidate Git blob identities equal A03's published A03 blobs; the API content fetch normalizes line endings, so local SHA256 values identify exact executed bytes separately.
- Independent recursive auditor: `PASS_DIAGNOSTIC_SCOPED`, 10 reconstructed rows, zero A02 differences, fixed discriminator mismatch.
- Construction unit tests: 2 passed (pre-freeze).
- Raw outputs and run environment are retained under `formal_a04/` and `RUN.json`.

See `SHA256SUMS` for exact local-byte hashes and Git blob identities.
