# Issue #5375 T0-v3: half-open and fallback boundary report

## H / T / D / C / U outcome

**PASS_CIRCUIT_BOUNDARY_SCOPED** in this finite discrete-event state-machine replay.

- Nine frozen rows, 9/9 exact candidate/oracle matches.
- A current, non-contradictory verified probe closed its own half-open generation.
- A semantic contradiction mislabeled `TRANSIENT_TIMEOUT` reopened the circuit; the classifier string alone did not close it.
- A prior-generation completion was ignored without replacing the active current-generation probe.
- Of two same-generation probe requests, one permit was accepted and one denied.
- Stale evidence and expired completion did not close the circuit.
- Containment/UNKNOWN fallback stayed non-authoritative; attempted `ADMIT_ACTION` was downgraded to UNKNOWN.
- Authority outcomes/grants, verifier dispatches, model/GPU/network calls: all zero.
- Eight construction tests passed. The independent raw-only auditor returned errors=[]; its selected mutation suite passed 6/6.

The complete frozen H/T/D/C/U matrix and scenario definitions are in [FREEZE.md](FREEZE.md). No prior T0-v1 or T0-v2 evidence was edited or replayed.

## Provenance and execution

- Intake main: `cf8ad3d1a675af9e64c1be356d03e35699548b33`.
- Allocation: `circuit-breaker-5375-half-open-boundary-20260930-01`.
- Runtime: Windows / CPython 3.11.9 with `python -B`.
- One-shot runner: `python -B -c $bootstrap`, with exact GitHub-readback `breaker.py` and `run_t0.py` streamed into memory and compiled without rewriting source. No local result files.
- Git blob SHA-1s: breaker `f58c822487a65b37a7832278c5eb1e39a64ffd39`; corpus `db1ed31c93ebb92521a0a5d7c48d5f0012dc9747`; runner `1dd9426eab867f2c03a980c46f490286a06c1378`; construction tests `4a314205723b34cb28989176e312fd30209435d0`; freeze `e0b4396e52f9cf691565f706bea9017fb643afa3`; auditor `d1488ecff6be2e291dc855b08d9861a4bba52fed`; audit mutation tests `f04c2720eacc98d192aa6042b200eedb2de6ab28`.
- First raw outcome: [FORMAL-01.json](FORMAL-01.json). Audit: [AUDIT-01.json](AUDIT-01.json).

Transparency note: the literal raw-only auditor source was authored after the one-shot runner output, then executed as a separate process against the preserved raw. The auditor imports no candidate code and compares all nine rows to its own literal transition table, but it was not itself source-frozen before the run. Treat its result as a useful integrity check, weaker than a preregistered independent auditor. Six deep-copy mutation controls verify selected denominator, source, transition, authority and disposition fields; they do not repair that chronology limitation.

## Resource and claim boundaries

The current #5085 queue note prohibits Docker CLI use until an owner release and exact coordinator allocation; C: had 0 bytes free. Performed only a tiny host CPU memory-streamed replay; no Docker/OrbStack, model, GPU, network, GUI/input, verifier dispatch or external side effects. The raw explicitly records `container:false`.

This demonstrates the stated state transitions only in a serial discrete-event model. The duplicate probe arrivals are deterministically ordered, not actual concurrent threads. No runtime locking, scheduler contention, cancellation, threshold calibration, semantic-classifier observability, correlated-failure resilience, latency, task/GUI safety or production claim follows. The earlier toy oracle and these synthetic cases do not establish real dependency-failure rates.
