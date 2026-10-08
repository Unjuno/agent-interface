# Issue #59 — owner pagination integrity T1

**Decision: `PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND`.** On the exact current-main global-owner helper, a bounded synthetic visibility model found 5 admissible incomplete responses in 44 cases where `total_count == len(rows)` despite duplicate IDs concealing an omitted distinct matching run. The helper admitted the current run; an independent oracle over the complete synthetic run set rejected it. Raw-only audit: PASS, no errors.

## H / T / D / C / U

- **H:** An incomplete but apparently count-complete API view can admit an owner if duplicated rows hide a missing distinct run.
- **T:** Frozen helper SHA `0b1056c6cbd95288d2c1934a471d2a04b9c000cd1114da7a49310afc850b87fd`, frozen existing test SHA `f72f369e2e3d9697108ae905894da33f92198fc2aa7e30abaa84d7efb5838dc6`; run existing tests (12/12 PASS), enumerate synthetic full run sets of size 2–3, visible subsets, current IDs, and duplicate-row variants; independently audit all 44 outcomes.
- **D:** 44 cases; 5 counterexamples; `PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND`. Independent audit `passed=true`, `errors=[]`, counterexample count 5. Candidate raw SHA-256 `67c910b3ea5821c4f561f92464698829213ee8757be33612682b6784c705c5da`; audit SHA-256 `7d68508e0448fbe9b629ad0a29ee6f2c891ebd31d8b5ce0f3565a17706d4a2ef`.
- **C:** The test's relevance depends on whether the real Actions API or its client can produce duplicate rows across pages while reporting a matching total count. The model does not assert that it does.
- **U:** No real API, workflow, dispatch, race, Docker, GPU, MAP01, model, GUI or input. No production/helper fix is included. No live allocation is authorized and #59 remains open.

The exact source was fetched from main intake `5eb0c44f2fc3d851b6469ceabda57b091ec76668`; its helper blob was unchanged on main `5eb0c44f2fc3d851b6469ceabda57b091ec76668` (`f07f928f67a7a6c670d399efb23d67246506c802`). The twelve existing tests passed. The new audit tests passed 2/2, Python compilation and `git diff --check` passed.

## Execution deviations

The first unittest invocation used an invalid module-path form and returned an import error; a subsequent correct `unittest discover` run passed all 12 retained helper tests. No source or result was changed by the failed invocation. Candidate and independent audit each executed once; no retry of a formal/live allocation occurred.

See `raw.json`, `audit.json`, `plan.md`, `candidate.py`, `audit.py`, and `test_audit.py` in this directory.
