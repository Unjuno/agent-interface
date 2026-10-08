# T12 — explicit incomplete scope and strict schema audit

## H / T / D / C / U

**H.** A finite numeric gluing record can avoid presenting partial-subgraph optimization as a full-cover certificate, while a raw auditor rejects malformed schema/types before semantic reconstruction.

**T.** Four frozen relation fixtures × four tolerances × three contracts × three action classes produce 144 rows. The candidate enumerates all 125 assignments on the fixed grid; the independently implemented Fraction oracle reconstructs each output. Incomplete records retain a separately named observed-subgraph diagnostic, but omit full-cover minimax and witnesses. A strict raw schema validator and fifteen corruption controls exercise type/domain/scope boundaries.

**D.** PASS scoped iff all 144 rows agree with the oracle, complete-case minimax and policy boundaries remain exact, incomplete output is UNKNOWN/non-admitting with explicit observed-subgraph-only scope and no full-cover minimax/witness, and all 15 non-identity mutations are rejected.

**C.** Fixed finite fixtures, integer ticks, exhaustive three-variable grid, and a strict enumerated input domain. This is not a general-purpose interface evidence API.

**U.** No calibrated tolerance/uncertainty, general sheaf solver, real context/overlap semantics, freshness/provenance, causal ordering, authority precedence, GUI/model/task effect, runtime safety, or product claim.

## Review-driven scope

Independent review of T11 confirmed complete-case arithmetic and the frozen 144-row agreement, but found that incomplete evidence serialized a minimax/witness without machine-readable subgraph scope and that its auditor did not exercise strict schema rejection. T12 is a new frozen successor; T11 source, raw, audit, and report remain unchanged. `CONSTRUCTION_LOG.md` preserves a pre-freeze failure: Python `False == 0` caused two JSON-distinct type mutations to be misclassified as identity, followed by a separate relative-path command STOP. Canonical JSON byte comparison plus strict type validation corrected the construction suite before the formal freeze.

## Frozen execution and outcome

- Allocation: `gluing-numeric-schema-5537-t12-20261001-01`.
- Freeze commit: `ba6d8fdad`; base: `d077494b50341f638e6d66f63e817ec48923768d`.
- Environment: CPython 3.14.5, Darwin arm64, host-only. #5085 showed competing CPU/OrbStack requests but no exact exclusive T12 lease; the shared lane was not used. No GUI, model, network, input, or external effects.
- Construction on refreshed main: 5/5 tests pass; 144 generated rows match the independent Fraction oracle; 15/15 corruption controls are non-identity and rejected; py_compile, analysis index (245), workspace index (148), and diff checks pass.
- Formal candidate: one invocation of `python3 -B research/analysis/gluing_numeric_schema_5537_t12_v1/run_experiment.py`, exit 0; 144 rows. Raw SHA-256: `fec25b2be39af8059530ae69cad1b58124566e706a43dc7e06400b12fa172126`.
- Independent audit: one invocation of `python3 -B research/analysis/gluing_numeric_schema_5537_t12_v1/audit_raw.py`, exit 0; `base_errors=[]`; 15/15 non-identity mutations rejected. Audit SHA-256: `9287d4a4f66813c741637b31894370c33bfa84aa58002d658c9a913adf9a8baf`.

| Case | Observed-subgraph minimax | Full-cover minimax | Scope / status | Admitted rows |
|---|---:|---:|---|---:|
| exact cycle | 0 ticks | 0 ticks | full cover / GLOBAL_SECTION_CERTIFIED | 36 |
| near cycle | 2 ticks | 2 ticks | full cover / NO_GLOBAL_SECTION below tolerance, APPROXIMATE_SECTION at or above | 10 |
| far cycle | 4 ticks | 4 ticks | full cover / NO_GLOBAL_SECTION below tolerance, APPROXIMATE_SECTION at tolerance 4 | 5 |
| missing context | 0 ticks on observed edges | `null` | observed-subgraph-only / UNKNOWN; no global witnesses | 0 |

All complete-case T10 policy boundaries remain unchanged: exact sections admit; approximate `exact_only` admits none; `reversible_approximate` admits reversible/compensable only; explicit opt-in permits approximate irreversible actions only within tolerance. The incomplete result exposes no full-cover residual or optimal witnesses and never admits.

## Raw artifacts and frozen source hashes

- `raw/formal.jsonl` — SHA-256 `fec25b2be39af8059530ae69cad1b58124566e706a43dc7e06400b12fa172126`
- `raw/audit.json` — SHA-256 `9287d4a4f66813c741637b31894370c33bfa84aa58002d658c9a913adf9a8baf`
- Frozen source hashes, commands, environment, and one-shot protocol: [`FREEZE.json`](FREEZE.json).

This scoped result hardens serialization and auditing for the fixed synthetic model; it does not establish that real partial interface evidence can be safely glued or that any tolerance is calibrated.
