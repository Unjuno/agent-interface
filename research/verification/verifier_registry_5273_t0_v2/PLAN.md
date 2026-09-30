# Issue #5273 T0 v2 successor

## Review-driven delta

This is a separate immutable successor to v1. It consumes validated #5268 `verification_ir.v0.1` documents, makes accepted and output evidence roles explicit, makes hard incompatibility outrank temporary unavailability, and independently audits one-to-one row identity and raw allocation/source bindings. V1 and its host outcome are not edited.

## H/T/D/C/U

- **H:** A versioned authority-neutral descriptor snapshot can classify valid #5268 checks before dispatch and distinguish hard incompatibility (`REJECTED`) from missing/unqualified resources (`UNAVAILABLE`), preserving cost-estimate provenance.
- **T:** Ten frozen plans over real #5268 schema rows: warm feasible CPU; unsupported-but-valid primitive; wrong accepted evidence role; wrong output role; stale version; missing verifier; unavailable multimodal/GPU; cold budget violation; side-effect prohibition with unavailable network plus stale version; impossible deadline. Compare decisions to literal constants embedded in a raw-only auditor distinct from the candidate.
- **D:** Exact case IDs, check IDs, statuses, reasons, estimate basis, and zero dispatch must agree; duplicates, omissions, extras, changed allocation/base/schema and input/hash mismatches fail audit.
- **C:** Capability declarations can still be false/stale; synthetic cost values can be inaccurate; fixed fixtures may miss descriptor edge cases.
- **U:** Construction/preflight only. No backend invocation, verifier correctness, actual timing, scheduler benefit, concurrency, runtime integration, or action authority. Existing #5268 IR and #5269 coverage remain unmodified.

This run is host construction only unless an exact resource lease is independently granted. It must not reuse or relabel v1's allocation/result.
