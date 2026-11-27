# Grounding failure accounting through the shared caller

2026-10-16 JST. Main base `7322c0314c82ce598fcf4c3f3c120644b9a32f1c`;
tested repair `b765e7e33accdf9385a5fc9e7a8c92243476f3ab`.
Ordinary repair and construction checks. No provider/model, GUI/input, game,
WSL/container or formal allocation was run. Historical live results and frozen
source snapshots are unchanged.

## Missing integration boundary and repair

`PersistentGroundingModel.call` had a turn handle and, after a returned terminal,
per-turn usage, but raised a bare RuntimeError for an ineligible answer. Its
failure.json retained usage while the caller's failed attempt lost the call ID,
usage, image count and wait. Publication, validation and await exceptions also
discarded known metadata. The caller could not recover those facts from disk.

The model adapter now raises `GroundingCallError`, a RuntimeError subclass with
detached known accounting attributes and the original exception as its cause.
It uses the existing caller's failed-attempt metadata protocol; the caller,
planner and transport implementations are unchanged. The adapter makes no
additional RPC, retry, model call or input. The successful return shape and
borrowed-client ownership are preserved.

After a returned begin-turn handle, its ID and one submitted local image are
known even if awaiting completion fails. Before a returned handle, neither is
invented: the server may have received an uncertain start, so this is unknown,
not proof of zero remote work. Missing or rejected per-turn usage stays unknown.
Elapsed wait is the local adapter call interval, not billing or a bounded
provider response time. A failed call remains attempted, never completed.

## Executed evidence

- Nine new test methods compose the actual model adapter, persistent planner
  and adaptive caller v3. Only the RPC client is inert. Their ten retained rows
  cover failed/interrupted terminal, missing/invalid usage, denied failure/result
  publication, invalid completed answer, await timeout, start failure, and a
  successful model followed by unavailable task effect. Synthetic execute/effect
  callbacks grant no native authority and prove no application task success.
- The initial seven-method RED produced seven assertion failures. Adding start
  and invalid-usage controls yields the final nine methods. The complete pinned
  original model module fails eight assertions, zero errors, in that same final
  suite under both normal and optimized Python. Control source bytes are in
  `baseline_model.py.txt` with [CONTROL_SOURCE_PINS.json](CONTROL_SOURCE_PINS.json).
- Final affected caller/model/planner/catalogue selection: **22 modules, 104
  methods, zero failures/errors/skips**, normal and actual `-O`. This is not the
  full native catalogue or a live transport test. The first broad-run setup
  stopped before tests because a sparse-checkout JSON fixture was absent; its
  stderr is retained. The committed fixture was materialized and the output
  directory changed before the complete runs; no historical producer was run.
- [SOURCE_PINS.json](SOURCE_PINS.json) joins 38 current source/data files by AST,
  JSON or text-line semantics, with separate Git-byte and worktree-byte digests.
  `CONDITIONS.json`'s base identifies the tested repair head above. Its old-PR
  fields are inherited navigation context, not an ownership or execution grant.
  Complete streams and process receipts are retained. Four gzip archives retain
  full normal/-O suite records and baseline records; [RECORD_ARCHIVES.json](RECORD_ARCHIVES.json)
  verifies their uncompressed byte identities. Nonfinite values in other caller
  tests use the explicitly tagged JSON representation described in CONDITIONS.
- A separate saved-only input-to-ledger reader checks all ten new rows against
  the supplied RPC usage/status and rejects the pinned original rows. Both reader
  modes reject four copied contradictions: lost turn, lost usage, false success
  and an invented admitted image before returned start. Its stdout and process
  receipts are retained. The reader is not an independent application scorer.

The three `.py.txt` runners/readers are inert reference data with original local
path bindings, not registered actors. The new regression is registered once in
the existing protocol suite. No new review quorum or coordination Issue is added.

## Adoption and remaining work

Adopt this failure-accounting repair so the selected adapter can feed known
failed-call facts into the already-integrated ledger. `failure.json` or
`result.json` publication may still fail; in-memory exception metadata does not
establish durable retention, restart recovery or exactly-once remote execution.
Non-Exception process stops, uncertain start without returned ID, live provider
telemetry and actual application effect remain separate boundaries.

For #57, connect and qualify the selected actual task adapters, including all
calls performed inside adapters, then execute a permitted frozen matched
cold/warm/invalidation/repair comparison. Synthetic usage, an eligible model
answer and completed input are not independent task success, native release
bounds, matched efficiency or second-domain transfer. #57/#59 remain open.
