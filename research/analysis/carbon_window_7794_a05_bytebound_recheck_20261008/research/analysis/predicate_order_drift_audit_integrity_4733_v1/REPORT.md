# #4953 copied-evidence audit-integrity experiment

## Outcome

`PASS_AUDIT_GAP_REPRODUCED` on the one-shot Docker formal run for allocation
`predicate-order-audit-integrity-4733-20260928-03`. The unchanged 336-row baseline
passed in normal Python, `python -O`, and `PYTHONOPTIMIZE=1`. Each of the three
independent in-memory mutations also received `PASS_DRIFT_BOUNDARY_MAPPED` with
`errors=[]` in all three modes (9/9 mutation-mode cases). The independent Docker
auditor returned `INDEPENDENT_AUDIT_PASS` and independently rebound source,
archive, extracted raw, result content, controls, modes, mutations, and disposition.

Mutations: first retained row `weight = NaN`; top-level `development_alpha =
0.5`; top-level `truth_state_count = 99`. No mutated raw was written. The raw
archive and source hashes match before/after receipts.

## Frozen input and environment

- Source Git blob `1a6cc0e46b32d4cd6989aed118d003cce4cfe399`, SHA-256
  `28b207348b6279395670b282edcdc719ac1a653ff0e2dc09c987cf95526cf4d5`.
- Transport Git blob `c38dd2002f201d49b6fc261caff019550a4bf4bc`, SHA-256
  `474b6381e8381ed8cae12141303e4638539d12cf6cf8b1c999c630efae80efe7`.
- Extracted RAW.json: 186,739 bytes, SHA-256
  `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`, 21
  distributions × 16 truth rows = 336 rows.
- Container: pinned image
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  native `linux/arm64`, Python 3.12.14, network disabled, read-only root and
  source/input, 1 CPU, 512 MiB, 32 PID limit.
- Exact formal and independent-audit commands are in `FREEZE.json`.
- `RESULT.json` SHA-256
  `6cbfbd81b031dd0aa8d0b6c764b84a0b54160d1a3f83c26cd62a65370a2c1809`.
- `INDEPENDENT_AUDIT.json` SHA-256
  `80f242c5bef6cac618ffb5f5a1fa4ef78352e2da140e3b8271aa94cdc81ddd1b`.

## Provenance discrepancy disclosed

The captured runner's JSON labels its `allocation` as
`predicate-order-audit-integrity-4733-20260928-01`, a stale hard-coded constant.
The actual invocation used the pre-registered allocation-03 output mount and
the frozen revision-4 command; its output and audit are preserved byte-for-byte.
The independent audit checked scientific/input binding and result digest but did
not validate this allocation label. Treat allocation identity as established by
the frozen command, GitHub pre-registration, and output path, not by the stale
JSON field. This is a reporting defect and is not hidden or silently rewritten.
The experiment result remains bounded to this invocation and input only.

## Preflight STOPs and correction

Earlier attempts on allocations 01/02 stopped before target auditor execution.
The initial CLI invocation was malformed; a subsequent fresh start hit the
output-exists guard because code still read `sys.argv[2]` (the transport input)
instead of output `sys.argv[3]`. An earlier comment incorrectly attributed this
to bind-mount behavior; that diagnosis was corrected in the Issue thread. Those
allocations were not retried or pooled. Allocation-03 is the only scientific
result reported here.

Construction tests passed 3/3 under normal Python, `python -O`, and
`PYTHONOPTIMIZE=1` both on the host and inside the same pinned, network-disabled
arm64 Docker image; `git diff --check` passed. This finding is not a general
security certification, strict-JSON interoperability claim, or evidence about
the unchanged-byte numerical result, arbitrary corruptions, predicate quality,
or runtime performance. Successor work should bind finite numeric values and
all declared metadata to frozen provenance and rerun independent corruption tests.
