# Issue #6664 — observable quiescence certificate T0

Allocation: `OBSERVABLE-QUIESCENCE-CERTIFICATE-6664-T0-20261002-01`; frozen base: `9a573b00dc595e64d09387e567c85e10b61a46c1`; current integration base: `f0242a747`.

## H / T / D / C / U

**H — `PASS_METHOD_SCOPED` for the frozen finite protocol model.** The raw-only independent auditor reconstructed 1,191 cases and all 3,573 policy/snapshot checks with zero errors. `ACCOUNTED_QUIESCENCE` produced 128 `QUIESCENT` horizon decisions and 0 false certificates; the other 1,063 horizon decisions remained `UNKNOWN`. It stayed `UNKNOWN` at all 1,191 takeover-boundary and grace-deadline snapshots because no post-boundary observation receipt was yet available. Across all three snapshots, `EPOCH_ONLY` made 3,445 false certificates (3,573 decisions total) and fixed one-tick `TIME_DELAY` made 2,254 (2,382 `QUIESCENT` decisions). Every explicit post-boundary old-epoch admission was rejected in the frozen fixture.

The distinction is not that accounted quiescence always certifies: most schedules remain unknown. Its scoped result is that completion required operation-bound terminal evidence, a current backend-generation reconciliation after restart, matching release evidence for held input, rejection of stale admissions, and a fresh post-boundary observation covering preceding state. Lost/missing or contradictory evidence did not become success. All seven pre-freeze corruption controls failed audit as intended.

**T/C.** One frozen, deterministic standard-library host run on macOS arm64 / CPython 3.14.5; candidate invoked once, independent auditor invoked once; both exit 0. No Docker, OrbStack, WSLc, GUI, OS input backend, model, participant, external effect, or network operation was used. The Issue explicitly authorizes this simulator-only rung and disallows inference to a real backend.

**D.** The preregistered method gate passed: all 1,191 fixture identities were generated deterministically; the raw auditor reported zero errors; ACCOUNTED had no false certificates; both comparators had false certificates; stale old-epoch admissions were rejected; and predeclared corruption controls were caught. This is not a blanket proof of simulator soundness or backend behavior.

**C/U.** Results depend on authored event schedules and truthful receipts. A real backend may have hidden queues, non-cancelable effects, unreported held inputs, or receipts that do not correspond to semantic completion. The finite model does not establish actual OS queue drain, GUI effect completion, human takeover safety, latency/utility, or portability. A live adapter rung needs its own source-bound contract, authorization, and independent evidence; this T0 does not authorize it.

The distributed-systems analogy is deliberately narrow: Chubby sequencers illustrate sink-side stale-request fencing and its lock-delay fallback is described as imperfect; Lamport motivates ordering events rather than treating elapsed time as an ordering proof. Neither source validates GUI queue draining or application effects ([Burrows, OSDI 2006](https://static.usenix.org/events/osdi06/tech/full_papers/burrows/burrows_html/); [Lamport, CACM 1978](https://www.microsoft.com/en-us/research/publication/time-clocks-ordering-events-distributed-system/)).

## Overlap / integration

The 2026-10-02 main advance was additive and disjoint from this allocation's frozen files. Nearby work is retained unchanged: #5361 studies receipt/epoch-bound reclamation; #5817 conserves unresolved effect obligations; #6284 compares cross-handoff correction conservation against #24+#5817; #6310 studies source-complete predicate-relative no-change evidence; and the newly opened #6680 studies ambiguous residual diagnosis and safe discriminating observations. This T0 is specifically about an observable GUI input/effect/release boundary during authority handoff, not a replacement verdict for those results. No existing result was edited or rerun.

The adjacent Chubby and Lamport works support the analogy only; they are not novelty evidence for quiescence itself. The repository-specific discriminator remains whether a concrete backend can account for admitted operations, held-input release, and fresh post-boundary observation without upgrading unknown state to success.

## Reproduction and artifacts

- Frozen design, hypotheses, thresholds, and limits: [`preregistration.md`](preregistration.md)
- Source/fixture identity and pre-freeze construction gate: [`FREEZE.json`](FREEZE.json)
- One-shot raw events, independent classification, invocation record, exit codes, and artifact hashes: [`formal_run_01_20261002/`](formal_run_01_20261002/)
- Formal outcome: `formal_run_01_20261002/classification.json` = `PASS_METHOD_SCOPED`; both stored exit codes are `0`; artifact SHA checks pass.
- Construction/corruption tests: `python3 -m unittest -v` — 12/12 passed before freeze.

## Local validation

After refreshing onto `f0242a747`, the focused T0 suite passed 12/12. The 15 pre-existing unit-test suites invoked by the Analysis Index workflow passed 90/90 (102 tests total with this T0 suite); the workflow's frozen-source provenance check was run in an isolated temporary copy with its pinned historical workflow, SHA-256 matched, and all ten geometry-feasibility recovery tests passed. The separate human-return allocation-02 suite passed when run from the workflow's declared working directory. The repository analysis index (508/508), workspace index (156 reachable top-level directories), public navigation (26 documents / 1,466 links), Python compilation, formal artifact hashes, and `git diff --check` passed. Hosted Actions are separate and are not represented here as local passes.
