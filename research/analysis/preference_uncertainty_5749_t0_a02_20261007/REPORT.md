# Issue #5749 — evidence-bounded clarification escalation T0 A02

## Result

`PASS_METHOD_SCOPED` on a 7-case × 4-policy authored finite fixture. The independent auditor reconstructed all 28 rows with zero errors and rejected all 8 frozen mutations. This is a method-contract result only; it says nothing about human comprehension, burden, preference accuracy, GUI behavior, or benefit.

The evidence-bounded policy made one candidate offer, and only in the case whose ambiguity locus and unique candidate were explicitly marked offerable. It used 6 question units versus 8 for repeat-open, with zero false confirmations in both. Fixed-targeted used 5 units with zero false confirmations but no candidate-narrowing resolution; it is cheaper on this fixture. Always-offer used 4 units and made four candidate offers, three of which were unsupported by the fixture's `offer_allowed` boundary. All policies yielded on decline, stale response, or absence of an admissible candidate.

Thus the scoped hypothesis survives only in its narrow form: evidence-bounded escalation can produce one additional supported candidate-narrowing step over repeat-open without the false confirmations of always-offer. It does **not** dominate fixed-targeted on question cost, and this fixture does not establish real question resolution or human interruption benefit. Prefer fixed-targeted where the target is known and a candidate is not uniquely source-supported; preserve open/UNKNOWN for unknown loci and multiple supported interpretations.

The raw field `false_confirmations` is operationalized here as an **unsupported candidate offer** (offer not explicitly permitted by the frozen source-evidence flag). The fixture does not model a human accepting or confirming that offer; the count is a proxy for false-confirmation exposure, not an observed confirmation event.

## H / T / D / C / U

- **H:** After an uninformative answer, evidence-bounded escalation can resolve more eligible cases than repeating an open question without exceeding the false-candidate rate of always-offer.
- **T:** Seven frozen traces cover known/unknown ambiguity locus, one versus multiple candidate interpretations, explicit decline, stale choice version, and a forbidden-only candidate. Compare repeat-open, evidence-bounded escalation, fixed-targeted, and always-offer. An independent auditor reconstructs every decision, question count, support count, forbidden effect and false-confirmation classification.
- **D:** `PASS_METHOD_SCOPED`: 28/28 rows agree; 8/8 mutations rejected; zero forbidden candidates. In this fixture evidence-bounded yields one supported narrow candidate resolution versus zero for repeat-open, with 6 versus 8 question units and zero false confirmations. Fixed-targeted costs 5 units and remains a simpler competitor.
- **C:** Fixed-targeted is lower-cost when the ambiguity locus is known. Always-offer can appear efficient only by making unsupported candidate offers. Repeating open may be preferable when even a targeted question is not justified.
- **U:** Fully authored synthetic policy traces; no participant, model, GUI, runtime, preference ground truth, timing, interruption, task effect, privacy or authority study. A candidate offer is not an answer and does not authorize an effect. No universal superiority or human benefit follows.

## Execution and integrity

- Source base: `fa791fe937fb24245e785d9e22928b3f4a6a42ae`.
- OrbStack pinned `python:3.13-alpine`, `linux/arm64`, network disabled, read-only root and source, writable output-only bind mount; requested 1 CPU / 512 MiB / 64 PIDs (effective cgroup enforcement was not independently measured).
- Candidate: one invocation, exit 0. Independent auditor: one invocation, exit 0. Formal retries: zero.
- Formal raw and audit are in `results/formal02/`; exact command and hashes are in `FREEZE_A02.json`, `RUN_A02.json`, and `SHA256SUMS`.
- Construction tests: 4/4 pass; Python compilation and `git diff --check` pass.
- Formal01's own PASS output is preserved, but its post-run fixture-expectation mismatch is recorded in the sibling package's `CORRECTION-01.md`; formal01 is not counted as a valid Issue result and was not rerun.

## Reproduction

Run the `container_command` recorded in `FREEZE_A02.json` from the frozen source tree. Do not reuse the consumed allocation. A future changed protocol requires a new allocation/freeze.
