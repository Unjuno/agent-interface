# Issue #8581 T0 A01 — controlled feedback and raw-artifact bypass

## Scope and H / T / D / C / U

This is a deterministic finite method experiment for [Issue #8581](https://github.com/Unjuno/agent-interface/issues/8581), based on current `main` `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. It does not rerun or pool #8319 A01/A04 and uses no repository-private or real held-out data. It tests one authored updater/access graph only; authority is `NONE`.

**H.** With no raw-result route, CONTROLLED feedback will yield a smaller development-to-fresh optimism gap than FULL per-case feedback. When a separate route returns the raw development store, controlled feedback will lose that advantage. The independent access audit will detect the returned canary, distinguish denial from successful access, permit benign documentation, preserve UNKNOWN for an unmonitored route, and keep the fresh cohort sealed until lock.

**T.** Cross feedback (`FULL`, `CONTROLLED`) with artifact access (`SEALED`, `RAW_BYPASS`) over 12 paired seeds. Each seed has 10 development and 10 fresh opportunities and a fixed candidate menu: a lower-complexity stable candidate, a high-development/low-fresh memorizer, and a hard-vetoed unsafe candidate. FULL returns per-case development rows; CONTROLLED returns only a coarse improvement signal. The updater selects the best-development safe candidate if per-case data arrive through either channel, and otherwise chooses the lowest-complexity candidate with an improvement signal. The artifact graph records a benign public task document, a denied pre-lock route, a canary-bearing raw bypass, a separate fresh-store denial probe, an unmonitored-route UNKNOWN control, an explicit no-attempt control, and authorized post-lock publication. A hard-safety veto is separately disclosed immediately and exactly in every factorial cell. Fresh outcomes are held in the audit-only oracle and cannot enter pre-lock selection.

**D.** `PASS_METHOD_SCOPED` only if an independent auditor reconstructs all 48 paired trials and denominators; reproduces candidate updates from returned inputs only; detects every returned raw canary; distinguishes denied, returned, and no-attempt states; accepts the content-hashed benign document; marks an unmonitored route UNKNOWN; verifies pre-lock fresh-store denial and post-lock publication; discloses every hard veto without selection; and rejects 8/8 frozen mutations. The hypothesis disposition is `BYPASS_DEFEATS_FEEDBACK_SCOPED` only if the controlled/no-bypass optimism gap is below the full/no-bypass gap and controlled/bypass meets or exceeds the full/no-bypass gap. Any unknown main-path access or auditor mismatch yields HOLD/STOP; no retry.

**C.** A real candidate author may ignore raw outputs or choose another update rule; a fresh blinded cohort and lineage/exposure accounting may be more decisive than feedback shaping. The synthetic updater is deliberately fixed to make an information-path interaction testable.

**U.** This cannot establish actual researcher behavior, real artifact leakage, the completeness of a real access graph, any GUI-task population effect, or privacy. Public repository history and unlogged memory are outside the simulator. This is exact finite authored-method evidence only; no model, GUI, network, real private data, held-out answers, or shared runtime.

## Construction and formal gate

Construction tests and a separate temporary-output candidate/auditor replay precede freeze. Commit and push the source, data, update rule, and thresholds; preregister exact hashes on #8581 and verify remote bytes before formal execution. Candidate runs once; auditor runs once only after successful output and hash capture. Zero retries.
