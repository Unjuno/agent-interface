# Issue #4778 — fresh-seed Needle intent-capacity replication

This directory holds a provenance-corrected successor to the synthetic width
study in #4679. It keeps the scientific workload and gates, uses three fresh
seeds, and verifies all frozen source bytes and the exact local Docker image
before one formal run. #4679's data/result/audit remain unchanged.

## State

- Allocation: `needle-intent-capacity-4679-v2`
- Current phase: construction and pre-freeze only
- Formal seeds: 4153201, 4153203, 4153207
- Container image tag: `needle-pilot05:local`
- Expected image ID: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`
- Formal orchestrations consumed: 0

The final result and full SHA-256 manifest will be appended after the single
frozen allocation; this placeholder makes no outcome claim.
