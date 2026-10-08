# Issue #5970 × #5348 — causal-cut recovery reachability T0

## Result

**`PASS_METHOD_SCOPED`** for the finite synthetic question “does causal-cut validation reject nominal recovery readiness assembled from incoherent evidence, while retaining a valid same-epoch path?” This is not an empirical recovery, runtime safety, or product result.

Six fixed traces used three asynchronous streams (root evidence, surface focus/lease, and invalidation/release). The candidate exhaustively enumerated source-prefix-closed and parent-closed cuts. The independent auditor separately enumerated all subsets and reconstructed the legal-cut counts.

| Case | Graph-only | Cut-aware | Legal cuts | Interpretation |
|---|---|---|---:|---|
| Same-epoch positive | READY | READY | 8 | Valid causal cut and matching evidence epoch |
| Cross-epoch invalidation | READY | denied | 12 | `CONTRADICTORY` |
| Release sent, receipt delayed | READY | denied | 16 | `INCOMPLETE_IN_FLIGHT` |
| Missing causal parent | READY | denied | unknown | `UNKNOWN` |
| Reset midway | READY | denied | 12 | `CONTRADICTORY` |
| Genuine alternative root, wrong epoch | READY | denied | 8 | `CONTRADICTORY` |

All five adversarial bundles that graph reachability alone marked ready were denied by the cut-aware gate; the same-cut positive remained ready. Independent audit: six cases, zero errors, candidate/auditor cut counts agree. Construction suite: 6/6 passed.

## H / T / D / C / U

- **H:** Coupling staged-recovery dependency reachability with a causal-consistent evidence cut removes false READY outcomes from individually fresh but incoherent evidence, without rejecting a valid same-epoch recovery path.
- **T0:** Six source-frozen finite traces, explicit stream order, causal parents and messages; exhaustive cut enumeration; separate independent audit. Candidate and auditor each ran once. No model, GUI, network, user data, or actuation.
- **D:** `PASS_METHOD_SCOPED`: the valid positive remained READY; all five adversarial bundles were denied with `CONTRADICTORY`, `INCOMPLETE_IN_FLIGHT`, or `UNKNOWN`; all finite cut counts agreed with the independent oracle.
- **C:** A single atomic source might supply bootstrap evidence without a separate cut layer. This experiment does not quantify complexity, latency, or real-world frequency.
- **U:** A consistent cut proves causal compatibility only—not semantic truth, independent-root provenance, authorization, or external effect. No empirical black-start/recovery claim is made; Issue #5970's broader T1 remains untested.

## Integrity and scope

Fixture and code are pinned in `FREEZE.json`; candidate bytes and auditor bytes are pinned before adjudication in `AUDIT_FREEZE.json`. Raw candidate and audit outputs are write-once. The test is a scoped follow-up to the cross-issue direction recorded on #5970; it neither modifies nor subsumes #5348.

Docker Desktop's Windows service was observed `Stopped / Manual`, and the shared container lane was occupied/ambiguous. The deterministic Python standard-library experiment therefore ran as separate host processes, not in Docker. See `RUN.md` and `SHA256SUMS`.
