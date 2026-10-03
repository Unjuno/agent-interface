# Recovery of the first #6505 A01 setup STOP

The 16 tracked package files are preserved byte-for-byte from remote branch
`research/partial-order-6505-audit-orbstack-a01-20261003` at
`8786259b77c9219e449a1e32e8f7b2632126bc76`. That branch had no result PR at
the recovery check on 2026-10-03. Its frozen A01 run record reports one successor
auditor invocation, exit 1, `STOP_OUTPUT_NOT_EMPTY_OR_MISSING`, and zero formal
rows parsed. The package retains the operator mistake that placed
`container_config.json` in the required-empty output directory.

## Recovered stdout

The original worker checkout at
`/Users/taka/Documents/Codex/2026-10-03/agent-interface-6505-audit-orbstack`
still had HEAD `8786259b77c9219e449a1e32e8f7b2632126bc76` and an ignored
`results/formal_01/stdout.log`. The repository rule `.gitignore:6:*.log`
excluded it from the published branch. This recovery adds its existing 33
bytes unchanged at the original relative path. The output is exactly
`STOP_OUTPUT_NOT_EMPTY_OR_MISSING` followed by a newline.

- Recovered SHA-256:
  `a002acb8dbfcdbf469a36e4c060eaeba33d4b01c40e50c2f4ad2f0b0bebbed60`
- Recovered Git blob: `80a347f1b17341b042d935896fc60b1601838fab`

These identities were measured at recovery, not cryptographically bound before
the original invocation. The output agrees with the committed exit code and
run record. The exact original container ID was no longer present in OrbStack,
and the stored container configuration is a summary rather than a full Engine
inspection. Those provenance limits remain explicit.

## Validation and lineage

All 16 original tracked file blobs matched before delivery. The seven local
construction tests passed on the recovered source. They exercise the finite
model and mutation selection; they do not read or independently audit the
11,111 formal rows. The original frozen A01 was not invoked again.

The separately frozen A02 result is already on main through PR #6777 and
reports `PASS_INDEPENDENT_AUDIT_SCOPED`. A01 keeps its setup STOP and frozen
pre-run documents. This recovery does not change A02, the predecessor #4889
HOLD, or the open status of Issue #6505.

The recovery replayed all 31 executable check/test steps of the current
Analysis Index workflow locally on macOS with Python 3.14.5: zero failed
steps. The frozen workflow provenance input was restored and its declared
SHA-256 checked during the tests; the delivery workflow was restored afterward.
The index's separate 17 tests also passed. This is a local construction/CI
check, not the Ubuntu/Python 3.12 GitHub job or another A01 formal invocation.
