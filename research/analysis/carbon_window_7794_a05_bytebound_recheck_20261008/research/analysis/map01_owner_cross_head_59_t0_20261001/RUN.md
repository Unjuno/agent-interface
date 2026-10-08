# Formal run ledger

- Source freeze: b243aae9348b5f7266a6878ef2192bb91a464036 (parent main 4b7fe7837e4ee8c0d035ebfbf52baf014f042295).
- Owner-helper source commit/blob: 4b7fe7837e4ee8c0d035ebfbf52baf014f042295 / 85658f40c0fb689993d5034909326fd2364485d6; Git blob identity was checked in origin/main before execution.
- Fixture IDs/SHAs come from invalidated live-03 record blob 0292a415300336844d5c3f57c5466c68017affb8.
- Construction suite before freeze: python -m unittest -v test_construction.py, 3/3 passed.
- Existing frozen helper suite, read from origin/main: 10/10 passed. A two-row cross-head counterexample returned PASS_CANONICAL_OWNER for both runs.
- Formal candidate: python candidate.py --repo-root <frozen-main-checkout>; invoked once; exit 0. Stdout was directed to candidate_output.json at process launch.
- Independent auditor: python auditor.py; invoked once; exit 1 as preregistered for an invariant violation. Stdout retained in audit.json.
- Candidate output SHA-256: EA6B048CDB1595865F168A2FC17CE1E10F8E16BB92037C1AE326DFB137B0014C.
- Auditor output SHA-256: 516234C6A77652D7D3B47F6F700170B89A8FFD880AC41EFC4D36CAEC600C59F4.
- Candidate rows: 2/2 PASS_CANONICAL_OWNER, 2/2 allowed to enter. Audit: 2 distinct heads, 2 admitted, 1 invariant error. Preserve as FAIL; no retry.
- Runtime: Windows host CPU, Python 3.12; no container, GitHub Actions run, game, model, GUI, network request, GPU, or input.
- Scientific scope: selector counterexample only; no #59 efficacy or runtime conclusion.
