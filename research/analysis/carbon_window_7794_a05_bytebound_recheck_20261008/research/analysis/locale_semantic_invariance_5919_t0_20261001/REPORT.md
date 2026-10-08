# Issue #5919 T0 — locale-conditioned semantic invariance

**Outcome: `H_PASS_SCOPED_METHOD_PASS` on the frozen synthetic contract only.**

## H / T / D / C / U

**H.** A typed locale relation over expected effects accepts presentation-only changes, rejects wrong target/value/authority/input mappings, and leaves ambiguous translation equivalence UNKNOWN. At least one seeded semantic fault should be missed by English-only and visual-proxy baselines but caught by the typed relation.

**T.** Evaluated the frozen two-locale, eight-case fixture once. It contains two benign pairs (theme setting and decimal amount entry), five injected faults (misread translation, target swap, decimal parse mutation, keyboard-layout mismatch, weakened authority), and one ambiguous translation. Ran the separate auditor once against the fixture and candidate output.

**D.** Both benign pairs were PASS. The five faults were rejected at their intended stages: perception, target selection, effect verification/value, input encoding, and effect verification/authority. The ambiguous case was UNKNOWN. The independent audit returned `errors=[]`, validated every row and all three corruption probes, and reported `H_PASS_SCOPED_METHOD_PASS`. The candidate's English-only observation passed in all eight fixture rows but does not inspect localized behavior; the declared synthetic visual proxy missed all five faults. Exact rendered-string equality differed in all eight pairs, including both benign pairs. The H signal is therefore present only within this stipulated fixture.

**C.** A stronger locale-aware model/parser or ordinary symbolic validation may detect the same faults without a paired locale relation. The visual-similarity proxy is a frozen fixture boolean, not an image measurement. Translation/effect expectations are stipulated in the synthetic oracle and were not independently adjudicated by a locale expert.

**U.** This does not establish natural translation quality, multilingual model competence, real-app equivalence, assistive-technology behavior, user preference, general safety, or global novelty. It is a method-contract result over eight hand-authored cases only.

## Reproducibility and provenance

- Frozen source main: `cdfebdb125e0566d2cbe741c4925b94eb17b439b`.
- Fixture, preregistration, candidate, independent auditor, outputs, runtime notes, startup-attempt ledger, and invocation counts are retained beside this report.
- Candidate and auditor each executed once in separate Codex V8 isolates; no retries or startup failures.
- No Docker/container, GPU, model/provider, network call, host subprocess, local file write, or GUI was used. This finite string/record contract is CPU-only by construction; current host C: and Temp volumes also reported 0 free bytes and `docker info` remained unresponsive during a bounded probe, so no container lane was available.
