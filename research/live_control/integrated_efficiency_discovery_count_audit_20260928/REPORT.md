# Integrated-efficiency discovery count audit — 2026-09-28

## H / T / D / C / U

- **H:** The current integrated-efficiency plan's discovery totals agree with its authoritative `integrated_efficiency_discoveries_v1.json` ledger.
- **T:** A frozen, read-only Docker Desktop audit of plan and ledger at base `edbb9c56b6d417705eb37bc5d03facd16743f628`; a separately implemented raw-only independent reconstruction; then a corrected-plan Docker regression in the additive branch. Each run has a separate output directory and frozen inputs/source hashes.
- **D:** The ledger contains 8 entries: 3 `interface_mismatch` and 5 `benchmark_setup_accounting_defect`; all IDs are unique and required provenance fields are present. Run 1 returned `FAIL_PLAN_LEDGER_COUNT_INCONSISTENCY` (exit 1) and recorded one declaration as 6; its regex missed the other declaration because a line break split “six current”. Independent run 2 passed all 4 reconstruction/control checks, confirming both original declarations were 6 and the ledger count was 8. We corrected the two plan references to eight without changing the ledger or predecessor evidence. Run 3 returned `PASS_CORRECTED_DISCOVERY_COUNTS_SCOPED` (exit 0); all 3 controls passed, including rejection of a one-count mutation and parsing wrapped whitespace. The runner parser limitation remains recorded as a finding, not retroactively erased.
- **C:** Docker Desktop 28.5.1, `desktop-linux`, cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/amd64`), no network, read-only source/inputs, 0.10 CPU, 128 MiB RAM, 16 PIDs. The audit did not import runtime modules or invoke any model, GUI, provider, or action path.
- **U:** This establishes only that two plan counts were corrected to match the eight-entry ledger and that this narrow count check passes. It does not establish whether discoveries were correctly resolved, whether overhead totals are correct, or whether the integrated path is efficient, safe, or product-ready.

## Findings and follow-up

The ledger remains unchanged as the source of truth. Both plan references now say eight; `validate_corrected_plan.py` exercises wrapped whitespace and a mutation control. The first-run raw, independent reconstruction, and post-fix result are retained under `result-01/`, `result-02/`, and `result-03/`. No integrated-efficiency formal allocation was repeated. This audit does not change the global roadmap or claim the Issue #57 milestone complete.

## Reproduction and evidence

The invocations used the pinned image and constraints in the freeze records (`--network none`, read-only source mounts, output-only writable mounts, 0.10 CPU, 128 MiB, 16 PIDs). The immutable outputs are:

| Run | Outcome | Raw/result SHA-256 |
| --- | --- | --- |
| `result-01/raw.json` | Initial discrepancy; exit 1 | `c040c8dd9708c22317ba79c267310973c8d539847c7ba103b600f3eb4f89b98b` |
| `result-02/audit.json` | Independent reconstruction passed 4/4 controls | recorded in the file |
| `result-03/result.json` | Corrected-plan audit passed 3/3 controls; exit 0 | recorded in the file |

Docker Desktop reported version 28.5.1 and context `desktop-linux`. Run records and exact source/input digests are preserved alongside their outputs. These are bounded static documentation/ledger checks, not a runtime benchmark.
