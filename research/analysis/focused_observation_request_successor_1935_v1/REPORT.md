# Report

Status: `PASS_FOCUSED_REQUEST_VALIDATION_SCOPED`

The finite fixture enumerates 256 frame/request combinations. The candidate accepted 16 and rejected 240. An independent auditor recomputed the same 256-case oracle and obtained 16 valid and 240 rejected cases.

Required fail-closed properties held:

- epoch mismatch rejected;
- identity mismatch rejected;
- non-uncertainty reason rejected;
- out-of-bounds and empty regions rejected;
- matching in-bounds uncertainty requests accepted.

The candidate serialization SHA-256 was `5c2699e993fd163a1a01c72c3905b46c8f364e329a8ddef47c37bb713952b936`.

Local Docker reproduction used Docker Desktop 29.8.0 and `python:3.11-slim`; candidate, independent audit, and corruption controls matched. This remains fixture-scoped and makes no model, GUI, runtime, authority, or production claim.
