# Issue #5865 — negative evidence delivery T0a

## Status and scope

This is a new, finite CPU-only experiment for the 2026-10-03 #5865 reuse/
delivery refinement. It does not rerun the consumed query-completeness T0, alter
the #4174 historical results, execute a GUI/model/runtime, or grant authority.

## H / T / D / C / U

**H.** In a finite three-tier delivery model, immutable source-evaluation
deadlines plus typed route-failure records prevent false freshness and false
absence while retaining valid repeated-query reuse and healthy independent
routes. The naive sliding, untyped control will expose planted errors.

**T.** Compare (A) no reuse, (B) untyped/sliding-expiry negative reuse, and (C)
typed origin-bound evidence. A standard-library simulation covers cyclic
forwarding, exact expiry, changed predicate, insertion plus invalidation,
missing writer coverage, unknown clock mapping, route timeout with a healthy
independent route, forwarded failure cooldown at/after retry eligibility,
bounded failure-record retention, eviction, and a fresh independent source
re-evaluation. Every logical producer/request has an ID; raw events record
source and route attempts, typed state, retained entry/byte counts,
unknown/negative results, and authority=false. The separate oracle fixture
records hidden target truth.

**D.** `METHOD_PASS_SCOPED` only if the naive controls exhibit false freshness,
target-present false negatives, unsupported completeness claims, and healthy
route suppression; typed handling avoids all false-negative/expired-origin
reuse, refuses missing provenance, expires at the original deadline, preserves
valid within-window reuse with fewer producer attempts than no reuse, permits
healthy route B after route A fails, accounts for every request and retained
byte/entry, emits no authority, and passes every independent corruption
control. Otherwise retain `FAIL_METHOD` or `HOLD` without retry.

**C.** Fixed integer time, deterministic source outcomes, a three-tier forward
chain, a single target query family, explicit writer-coverage and clock-mapping
bits, and the frozen retry deadline. The fixture tests policy distinctions;
its timing/cost values are not production estimates.

**U.** No real GUI inventory producer, cross-process clock, receipt transport,
cache implementation, request latency, target-effect oracle, or production
failure-domain map is exercised. Passing this fixture cannot prove that a
real negative certificate is complete or remains current.

## Reproduction protocol

Freeze the repository/source/docs, Python environment, candidate and auditor
hashes before one candidate invocation. Retain that first output unchanged.
Run the independent raw-only auditor once on that output. The auditor must not
import the candidate and must reject expired-origin forwarding, predicate
drift, healthy-route suppression, duplicate raw events and a missing producer
receipt. A failed result is retained; no candidate retry is permitted.

## Decision and provenance

Issue #5865 remains open and unassigned. The issue's earlier query-completeness
T0 is already consumed and retained in main; this package tests only the later
reuse/delivery-boundary hypothesis. Main at freeze:
`19a6b723e58ccfd2b8265e88659589ef9223fcc9`. A01 is preserved separately as a
pre-candidate freeze-integrity STOP and is not a scientific result.
The exact source and environment hashes are in `FREEZE.json`.
