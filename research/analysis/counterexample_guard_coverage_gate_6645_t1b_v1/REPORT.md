# Issue #6645 T1b — isolated coverage-gate counterfactual

## Disposition

`PASS_COVERAGE_GATE_ISOLATED_SCOPED` for this frozen five-row synthetic
allocation. One candidate and one separate raw-only auditor invocation ran in
pinned OrbStack containers; each exited 0, retries 0. The independent auditor
reconstructed all five gate-disabled/gate-enabled pairs with zero errors.

## Result

With candidate-visible observations held fixed and the gate disabled, the
hidden harmful row was admitted. Enabling only the coverage gate returned
UNKNOWN because the frozen contract requires `modal_occlusion`, but that
predicate is not covered or present in candidate-visible input. A safe row with
byte-identical candidate input also returned UNKNOWN, as required by
non-identifiability. Complete-coverage valid and known-harmful controls stayed
ADMIT and REFUSE, respectively. An explicitly unregistered family returned
UNKNOWN only with the gate.

## Correction and lineage

This allocation follows the append-only erratum for merged T1. T1's original
source, result, hashes, PR #6800 and merge remain unchanged. Its comparator did
not isolate the gate because T1's candidate directly evaluated the modal
predicate while its legacy comparator did not. T1b runs one observation-limited
candidate function twice with only the gate boolean changed, and physically
withholds the oracle file from the candidate container.

## Limits

The externally supplied family registry is assumed complete for this authored
fixture. T1b does not prove how to discover unregistered unknown-unknowns,
validate ontology completeness in a real skill, or establish live cache/GUI,
user, product-safety, or performance behavior. The comparator is a deliberately
bounded pure synthetic guard. Docker memory/swap settings do not prove
host/cgroup enforcement.

See `FREEZE.json`, `RUN_RECORD.md`, `T1_ERRATUM.md`, and the checksummed raw
artifacts for exact source, isolation, and execution evidence.
