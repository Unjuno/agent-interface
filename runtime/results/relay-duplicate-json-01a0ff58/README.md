# Public relay duplicate-key repair — ordinary construction

Issue #6869 / PR #6879; worker `01a0ff58-ba92-7fd2-9317-d75b43383005`;
FINAL-v5. This extends the same public JSON-lines admission repair with a
different concrete decoder defect. The earlier finite-number evidence remains
unchanged in `../relay-finite-json-01a0ff58/`, bound to its original sources.

H: every object in an unambiguous request must have unique decoded JSON keys.
Refuse duplicate keys before SDK entry and request-ID consumption; preserve
ordinary finite/integer/string values and unique keys in distinct objects.

T: eight explicit duplicate-key inputs and eight positive controls, each with a
fresh relay, compare the already finite-float-repaired source from
`fe4bc0c6fe51acf5a407014fddccff6c5239b8df` against the added per-object key guard.
The baseline is exactly the prior evidence's candidate source. The SDK-shaped
client records calls and returns an empty real MCP `CallToolResult`; it sends no
backend input. Each initial request is followed by a valid request with the same
ID to distinguish refusal before consumption from refusal after admission.

D: retained 32 rows reconcile under a separately implemented finite raw-only
oracle. Baseline dispatches all eight duplicate-key inputs; repaired source
dispatches zero and accepts the valid same-ID follow-ups. All eight positive
controls are forwarded unchanged by both sources and their accepted IDs cannot
be replayed. Twelve effective raw mutations are rejected, including missing or
duplicate rows, false dispatch/refusal, ID consumption, bool/int confusion,
changed forwarded input, source/case binding and SDK/follow-up identities.
`audit.json`: `PASS_ORDINARY_DECODER_REPAIR_SCOPED`.

C: this is an exact authored parser/admission boundary, not a distributional
experiment. Conflicting or equal duplicate values are both refused; decoded
Unicode escapes can identify the same key. Case-sensitive names, repeated names
in different objects, Unicode escapes without a duplicate, nested arrays and
duplicate-looking text inside strings remain valid. The finite-number guard is
retained. The audit imports no relay, probe or MCP source but is by the same
author; it is not a nonauthor committee vote.

U: no GUI, physical input, task effect, performance, model, container/WSLc, or
cross-platform success is established. This is ordinary test-first engineering,
with zero formal allocation invocations; no consumed experiment was replayed.
The first red run retained seven failing duplicate cases and one positive
control. The null-first duplicate was added afterward and is also present in
the separately recorded source-bound matrix and final regression. The exact
uncommitted first-red test source and its endpoints were not captured; do not
treat that log as a prospective formal freeze. Source/matrix hashes and probe
endpoints are recorded in `SOURCE.json` and immutable `raw.json`.

## Local validation and retention

Windows 11 x64 / CPython 3.12.14 / MCP 1.30.0, committed executable source
`e7603c927b5cb48d89207f660f9b7b3e52473b18`, incorporating main
`4bd391e` (full identity in `SOURCE.json`):

- CLI/API and relay: 129 discovered, 123 passed, six Linux-only skips.
- MCP server/clock: 27/27; intervening manifest enum/kernel regressions: 26/26.
- Compile CLI/host/motor/selector: exit 0.
- The portable relay runs from the committed archive outside the checkout with
  the real SDK and no backend input. Unknown native tool, exponent overflow and
  duplicate ID refuse, then unchanged ID 1 lists public tools; validation and
  close succeed without opening an input connection.

The final diff adds seven protocol-documentation lines; an initial CRLF
expansion was corrected before these checks. `EXECUTION.json` retains actual
command endpoints and process statuses. Public stdout replaces local workspace
paths only; `PUBLIC_LOG_PROVENANCE.json` binds original and published bytes,
with originals retained privately. Raw/source bytes are unmodified.

`RETENTION.json` verifies all 29 original evidence Git blobs are unchanged and
all 28 original manifest entries match. That source remains a historical
candidate; the new source snapshot describes the extended runtime. Neither
original raw nor its auditor was rerun to update the old result.

The new files are explicit construction/audit entry points under a result
directory. They add no runtime import, test-discovery wiring or workflow.
The proposal outside this evidence will supersede content-v1 before any votes
can authorize the changed head. Two digest-bound nonauthor content votes and a
later exact-base/tree combination check remain required for main application.
