# #5890 intake-versus-test denominator A01

## H / T / D / C / U

**H.** A typed, ordered intake ledger will distinguish untested ideas from formally started tests: screened-out ideas remain visible in the qualitative intake funnel but do not enter the statistical test family, while a formally started negative trial remains in the started-opportunity ledger even if later abandoned. An independent raw-only auditor will reject attempts to erase that negative or misclassify deterministic checks as statistical evidence.

**T.** One fixed synthetic 19-row stream: 12 screened-out ideas (duplicate, infeasible, low-value); four started claims (FAIL then abandoned, PASS, HOLD, STOP); and three deterministic method/safety checks (PASS, FAIL, hard-safety FAIL). The candidate emits a typed funnel and separate started/statistical-family ledgers. A distinct auditor reconstructs them from the frozen input and tests five frozen corruptions: omit an intake row, reclassify the abandoned started negative as untested, omit a started STOP, invent a p-value for a deterministic check, and remove a hard-safety failure. Host Windows CPython 3.11.9, standard library only; no network, WSLc, container, GPU, model, GUI, game, or input. One candidate invocation and one independent audit, no retries.

**D.** `PASS_METHOD_SCOPED` only if the 12 untested ideas are preserved but absent from the statistical family; all four started opportunities, including the abandoned FAIL and STOP, remain visible; only the three predeclared eligible claims enter the statistical family; deterministic and safety rows are never assigned inferential p-values; the auditor exactly reconstructs the output; and all five corruptions are rejected. Any mismatch is retained as FAIL/STOP, never repaired or rerun.

**C.** This tests ledger bookkeeping on one authored stream, not statistical validity, family-wise error control, FDR, or whether intake screens identify valuable ideas. The categories and expected counts are intentionally explicit; the experiment does not estimate real-world frequencies.

**U.** One deterministic method fixture only. No empirical multiple-testing guarantee, GUI/model efficacy, user benefit, or safety/product claim.

## Freeze and launch rules

Allocation `PORTFOLIO-MULTIPLICITY-5890-INTAKE-A01-20261003`, owner Codex task `01a0b990-3d17-72f1-a908-9a2072104ce5`. Base is the exact GitHub `main` SHA recorded in `FREEZE.json`. Candidate and auditor are source-hashed before either formal invocation. Construction tests use inline examples only and do not import the formal input. Formal output paths are collision-checked absent. Immediately before launch, recheck `main` SHA, branch head, source/input hashes, Python version, output absence, host process inventory for this task, and available storage. A changed main/source or any failed check is a terminal pre-candidate STOP. The auditor runs once only if the candidate exits zero. Preserve exact first outcome; no retry or tuning.
