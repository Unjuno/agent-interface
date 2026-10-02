# PR #6521 WSLc construction STOP: preservation qualification

**Disposition: `STOP_PROTOCOL_COMMAND_MISMATCH`; consumed construction rung; no formal method result.**

This archive retains the earlier, distinct Issue #6509 WSLc allocation
`CLAIM-SCOPED-PARTIAL-VERDICT-6509-T0-20261002-01`. It is not the later OrbStack
finite-model result published by PR #6541. Neither record replaces the other.

## Terminal record

The single WSLc invocation executed only the runtime probe. The retained
container-creation timestamp is 2026-10-02 13:20:08 +0900 JST
(2026-10-02 04:20:08 UTC); it is not an independently established invocation
start time. The frozen construction command also required
`python -B -m unittest -v test_protocol`, which was omitted. The process exit
was 0, but this is not construction PASS. Construction invocations = 1;
formal candidate = 0; formal auditor = 0; retries = 0. The zero-retry rung
remains consumed. Preservation does not reopen or authorize any rung.

Read the unchanged [STOP record](formal_01_20261002/construction/STOP.json),
[RUN record](formal_01_20261002/RUN.json),
[terminal report](formal_01_20261002/REPORT.md),
[stdout](formal_01_20261002/construction/stdout.log),
[stderr](formal_01_20261002/construction/stderr.log), and
[exit record](formal_01_20261002/construction/exit.txt).

Retained observations identify WSLc 3.0.1.0, Linux/amd64, Python 3.12.14,
container `d6031c661294`, and cgroup `memory.max=1073741824`. The retained
warning says memory was limited without swap-limit support. These observations
do not establish complete resource enforcement or repair the missing unit
command. Host-side construction tests and earlier in-memory toy checks remain
development-only, non-formal evidence. This is an operator/protocol execution
failure, not positive or negative evidence about the proposed method.

## Immutable provenance and relocation

All 15 original files from PR #6521 head
`817fda5d451b363b19e6e3e84d5069601bc655f2` are retained byte-for-byte, with
unchanged Git blob IDs and file modes, at the same relative paths in this
archive. [IMMUTABLE_INVENTORY.json](IMMUTABLE_INVENTORY.json) records the
original and archive paths, exact Git blob IDs, byte counts and independently
recalculated SHA-256 values. All 15 Git blob IDs verified, and all seven source
SHA-256 values in the unchanged [FREEZE.json](FREEZE.json) matched. The copied
`formal_01_20261002/audit_source/auditor.py` is identical to `auditor.py`.
No declared frozen source hash is missing or mismatched.

The original source-freeze commit is
`6443152954db53b4805e0890d03bcff25c1aa342`. Its parent, the frozen base and
current PR merge base, is `b95e919d5844b8136f046868f89a28d73f4f5345`.
The PR's separately reported base snapshot is
`f6c6d2004bf57971e97fe889ab8e50d10a3b5ed7`; it is not the original branch point.

The original files intentionally retain their historical source path,
preregistration, commands and pre-run README wording. Relative artifact paths
inside RUN.json are relative to this archived package root. Historical
repository paths and the frozen `source_path` identify the original location
at the original immutable commit; they must not be resolved against the later
OrbStack sources now occupying that location. This qualification supplies the
terminal interpretation without rewriting the originals.

Byte verification establishes retained-file identity, not that those exact
bytes were mounted in the historical container. The actual-command record uses
`<frozen source>` and `<construction output>` placeholders, and the retained
files do not provide an independent source-mount hash or resource-owner lease
receipt. No missing evidence has been reconstructed or backfilled. No source,
unit test, candidate, auditor, runner, container, GUI, GPU or model execution
was performed for this preservation review.

## Separate successor and scope

The later [OrbStack report](../../REPORT.md), merged by
[PR #6541](https://github.com/Unjuno/agent-interface/pull/6541) at
`92d00da6bb19d005a857b4a2ea4094dc0385a834`, records a different 15-trace ×
3-policy finite result with candidate/auditor counts 1/1. This archive retains
the unexecuted 12-trace × 3-policy WSLc source and its construction STOP;
it must not borrow the successor's PASS or invocation counts.

The original fixture models one uncommitted-receipt crash case and has no
observed durable-write/restart or downstream consumer-effect trace. Its Boolean
`authority` also covers `COUNTEREXAMPLE`; it is not release/action permission.
These static scope limits do not alter the STOP and are not new experimental
findings. No GUI/live-verifier, real deadline, durable-storage recovery,
exactly-once behavior, model, safety, authority, or product benefit is established.

The prior owner record explicitly requires separate preservation without
replacement or retry:
- [Original construction STOP](https://github.com/Unjuno/agent-interface/issues/6509#issuecomment-5945545345)
- [Working-directory and crash-coverage erratum](https://github.com/Unjuno/agent-interface/issues/6509#issuecomment-5945677586)
- [Additive collision-preservation requirement](https://github.com/Unjuno/agent-interface/issues/6509#issuecomment-5945786096)
- [Post-merge instruction to preserve PR #6521 separately](https://github.com/Unjuno/agent-interface/issues/6509#issuecomment-5945979245)
- [Original PR #6521](https://github.com/Unjuno/agent-interface/pull/6521)

This nested archive does not change the successor's root REPORT.md, FREEZE.json,
candidate.py, other source or raw receipts, or existing analysis-index entry.
The existing root result/index links continue to identify the successor.
