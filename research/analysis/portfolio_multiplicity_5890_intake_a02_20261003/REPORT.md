# Issue #5890 intake-versus-test denominator A02

**Disposition: `PASS_METHOD_SCOPED` (one synthetic stream only).** The frozen candidate and separate raw-only auditor ran once each on the local Windows host. The auditor reconstructed 25/25 rows exactly and rejected all five preregistered corruptions.

The stream retained 16 screened-out ideas in the qualitative intake funnel while including none in the statistical test family. All five formally started claims remained in the started-opportunity ledger: two `TEST_STARTED_FAIL` records (one abandoned after an interim result), one PASS, one HOLD and one STOP. Four claims were prospectively eligible for the statistical family; the STOP had no valid p-value and remained an opportunity without entering that family. Four deterministic method/safety records remained separate and had no inferential p-values, including the retained hard-safety failure.

This demonstrates bookkeeping on one authored fixture only. It does **not** estimate FDR or error rates, validate p-values or intake quality, or support GUI/model/product/safety claims. Screened-out ideas are not treated as statistical null tests; the started abandoned negative is not erased. Allocation A01's pre-candidate main-advance STOP and #5890 allocation-02's earlier scoped result are unchanged.

See `RUN_RECORD.md` for commands, exact source/input/output hashes and invocation counts; `FREEZE.json` and `formal_input.json` are the preregistered source and stream.
