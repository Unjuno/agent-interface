# Issue #5865 T0a A03 — result

## Disposition

**`METHOD_PASS_SCOPED` for the finite protocol model.** The prospective
candidate ran once after `FREEZE.json`; the separate independent auditor ran
once and returned `PASS_AUDIT` for all 99 raw events and 30 case/policy rows.
All six corruption controls were rejected. There were no retries.

This A03 result repairs the A02 instrumentation/auditor/fixture defects under a
new allocation identity. It does not revise or relabel A02's
`STOP_AUDITOR_ERROR`; A02's output remains preserved and unaudited.

## Decision-gate evidence

- **Typed policy:** zero false-negative outcomes, zero unsupported negative
  claims, zero expired-origin reuse, and no authority grants. The event ledger
  reconciles request identities, retained entries and retained bytes.
- **Unsafe control:** three false-freshness witnesses occurred at the exact
  expiry boundary, after forwarding beyond the source deadline, and after a
  fresh source result expired. It also produced target-present false negatives
  for predicate drift, insertion, healthy-route suppression, and copied
  failure cooldown; it made unsupported negative claims for missing writer
  coverage and an explicitly forwarded unknown-clock receipt.
- **Reuse:** the typed policy retained valid reuse. Producer attempts were 14
  versus 17 for no reuse across the fixed case set; route attempts were 5
  versus 6. These are synthetic counts, not latency or production savings.
- **Route isolation:** after route A timed out, typed handling attempted
  independent healthy route B and returned its match. Forwarding a failure at
  time 4 preserved `retry_after=5` and `retained_until=15`; route A was eligible
  at time 6 and the record was gone at time 16.
- **Unknown clock:** A→B forwarding at time 4 was explicit. At time 5, typed
  and no-reuse returned `UNKNOWN`; the naive control reused the untyped
  negative.

Construction tests caught all three predecessor defects before freeze. The
four-test construction suite passed, including an in-memory full-candidate
check against all six auditor mutation controls. It wrote no formal output.

## Scope and limits

The evidence supports only this finite CPU-only standard-library model. It
does not test a live GUI inventory producer, cross-process clocks, production
cache/receipt transport, latency, or target effects. It cannot prove real
negative certificates complete or current and does not imply product/runtime
promotion.

## Reproduction and integrity

Commands are in `README.md`; pre-run source and environment identities are in
`FREEZE.json`. The first formal outputs and their SHA-256 values are retained
in `run-01/` and `run-01/SHA256SUMS.txt`.

`ENVIRONMENT.md` is a pre-run snapshot; its statement that the formal run had
not started describes the capture time before freeze and execution.
