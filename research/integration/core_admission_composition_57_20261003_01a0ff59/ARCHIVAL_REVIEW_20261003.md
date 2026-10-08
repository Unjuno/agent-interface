# Independent archival rescue: four-arm admission composition

PR #6880 source `6ace7a9b619efd9f51811e4293a4d62a3bbfb852`: all 43 original
files copied byte-identically; 42 manifest entries, 12 freeze-bound sources and
compressed raw receipt hashes reproduce. Original raw, source snapshots,
construction scripts, test export, publication failures and custody limits are
unchanged. This qualification and read-only tests are outside the old manifest.

New local checks: four archival tests (including six corruption controls) pass,
public navigation/workspace index pass, all 40 Analysis Index run steps pass.
The first full local runner completed its 40 checks but exited 1 because final
workflow restoration encountered a transient Git index lock. No lock was
deleted. The lock was later absent, the HEAD workflow restored, and a separately
logged second run completed all 40 checks plus restoration with exit 0. This
was tooling cleanup, not a scientific retry; the first failure log is retained
separately from the clean run, and no original study output was regenerated.

Function-level independent oracle verification exactly reproduces the entire
saved AUDIT.json over 9000 inputs per arm / 36000 rows. Mismatch counts remain
main 1654, enum-only 904, scalar-only 750, combined 0. Six directed raw
corruptions are checked only in memory. The historical four implementation
mutations are preserved as original records, not newly executed. No original
matrix runner, source mutation runner, runtime export, formal candidate/auditor
wrapper or container is invoked during recovery.

At rescue base `7c372cf6bea675f92939f861f34c8b0a192986dc`, the current promoted
`runtime/core_v1/contract.py` is byte-identical to retained `sources/combined.py`.
The earlier scalar repair was rescued independently through #7066. This source
identity does not turn the historical 78-method export into a current whole-suite
result: current tests have advanced, and the preceding rescue ran 87 core tests
plus 165 portable downstream tests separately. Those separate results are not
inserted into this original freeze or relabeled as this allocation's execution.
No production runtime or older contract snapshot is changed by this delivery.

**H/T/D:** preserved exact-type manifest/current-scalar conjunction and independent
finite raw oracle; archival integrity/saved-audit PASS only. **C:** authored
metadata failure counts are not public attack incidence or natural prevalence.
**U:** sessions, native backend effects, clock-domain consistency, concurrent
behavior, physical release, GUI, performance and user benefit remain unproved.
Source identity alone grants no input authority or general safety certificate.

Original pending V2 proposal/committee state and privately retained evidence stay
historical; no approval vote or application certificate is invented. User
authorized rescue before cleanup and local-first PR integration under normal
GitHub rules. Current shared-container availability was not requalified or
repaired; this recovery is a local read-only engineering evidence check.
