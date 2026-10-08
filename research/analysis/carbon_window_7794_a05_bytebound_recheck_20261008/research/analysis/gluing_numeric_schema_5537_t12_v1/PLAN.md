# Issue #5537 T12 — scope-safe incomplete output and strict audit schema

## H / T / D / C / U

**H.** A finite numeric gluing result can keep partial-subgraph diagnostics distinct from a full-cover minimax certificate, while a raw-only auditor with strict type/domain checks rejects malformed evidence rather than relying on Python's permissive equality (`False == 0`).

**T.** Use the T11 exact/near/far/missing relation fixtures, 125 assignments on eighth-unit grid `{0,2,4,6,8}`, four tolerance ticks `{0,1,2,4}`, three contracts, and three actions (144 rows). For incomplete evidence, serialize `minimax_residual_ticks=null`, scope `observed_subgraph_only`, its separately named observed residual, no global witnesses, UNKNOWN, and non-admission. The independent Fraction oracle reconstructs output. Strict schema validation covers exact keys/types, bool-vs-int, endpoints, target range, completeness, contract, and action. Fifteen preconditioned non-identity mutations include false incomplete-certificate promotion and malformed raw inputs/outputs.

**D.** PASS scoped iff all 144 rows independently reconcile; complete cases retain T11 minimax/status/policy boundaries; incomplete result is explicitly partial-only with null full-cover minimax, no witnesses, UNKNOWN/non-admitting; all 15 mutations are non-identity and rejected; construction tests and repository indexes pass. Any schema escape or false full-cover certificate is FAIL/STOP.

**C.** Fixed finite fixtures, integer ticks, exhaustive three-variable grid, strict enumerated domain. This is not a general user-input API or production validator.

**U.** No calibrated uncertainty/tolerance, general weighted sheaf semantics, freshness/provenance/authority model, GUI/model/task effect, runtime safety or product claim. T11's formal allocation, raw bytes, report and PR remain immutable; T12 is a separate successor.

## Successor relationship

Independent review of T11 confirmed the complete-case arithmetic and audit, but identified that the incomplete row exposed a minimax/witness without encoding its subgraph-only scope and that generic schema validation was absent. T12 addresses those boundaries without upgrading or editing T11.

## Freeze protocol

- Base: `d077494b50341f638e6d66f63e817ec48923768d`.
- Allocation: `gluing-numeric-schema-5537-t12-20261001-01`.
- Path: `research/analysis/gluing_numeric_schema_5537_t12_v1/`.
- Construction checks run before freeze. Formal runner once; separate independent auditor once only if runner exits 0. No retries or post-freeze source edits.
- Host-only unless an exact Docker/OrbStack lease is assigned before freeze; do not borrow shared allocation.
- Construction failure and repair are retained separately in `CONSTRUCTION_LOG.md`.
