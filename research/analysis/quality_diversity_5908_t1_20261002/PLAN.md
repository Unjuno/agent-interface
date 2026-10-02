# Issue #5908 T1 — descriptor archive method-sensitivity construction

## H / T / D / C / U

- **H:** An outcome-descriptor archive can retain both planted, independently labeled failure mechanisms in distinct behavior cells without exposing oracle labels to the selector; equal-budget fixed-order and pairwise-factor comparators quantify whether that representation adds discovery value in this fixture.
- **T:** Freeze 12 cases (8 legal, 2 invalid, 2 shortcut), a selector-visible feature map, an outcome oracle kept outside the selector, two independent post-run adjudication labels, uniform-seeded and pairwise comparators plus a descriptor archive at equal six-call budget, and mutation checks. Exhaustively enumerate the small pool. Candidate selection may use only case features and observed trace descriptors; not oracle labels, mechanism names, or future outcomes.
- **D:** `METHOD_PASS_SCOPED` only if descriptor archive retains both legal planted mechanisms in distinct cells within six calls, fixed-order and pairwise are run against the exact same pool/budget and their mechanism counts are reported, all invalid/shortcut cases are rejected before oracle admission, every call has one raw row, independent audit reproduces every selection/result, and descriptor/oracle/filter corruptions are detected. If a simpler comparator recovers the same mechanisms, no comparative discovery advantage is claimed. Otherwise retain the exact FAIL/HOLD.
- **C:** The hand-built pool and trace map may encode the desired discovery advantage; pairwise coverage may already suffice on a better factorization; exhaustive deterministic search can be simpler than QD; a bad independent oracle defeats all methods.
- **U:** Method-sensitivity construction only. No authentic failure distribution, useful GUI benchmark, controller benefit, precision/recall guarantee, safety claim, or T2 empirical discovery inference. The legal generator and planted basins are synthetic and deliberately small.

## Boundary

The selection policy receives candidate ID/features and, after evaluation, trace descriptors. It never receives truth labels or mechanism names. The evaluation harness and independent adjudicator hold those labels. A candidate can discover a mechanism only by spending an oracle/controller call on a case that manifests it. Budget is six admitted evaluations per selector; pre-admission invalid/shortcut rejection costs no oracle call but is counted and retained. Each selector operates on the same immutable pool, with no hidden-family or held-out claim.

## Execution

Issue #5908 T0 previously concluded `T0_HOLD_FORMAL_SUBSTRATE`; this is the separate no-model finite T1 expressly allowed there. Source base is `2106f20d61e4ef80cfcdbb2b694bbe10a07b454d`. Host CPython only: Docker Engine did not answer the bounded version probe; no container claim. No model, GUI, networked runtime, participant, or live controller.
