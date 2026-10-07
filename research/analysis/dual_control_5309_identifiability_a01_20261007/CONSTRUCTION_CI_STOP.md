# A01 post-run construction regression — STOP

After the one-shot A01 was already consumed and formally rejected, the local construction test was strengthened to encode expected behavior instead of source-string presence. It was run against the current candidate as a **construction regression only** (not a candidate allocation or scientific replay).

Command:

```text
node --check candidate.mjs
node --check auditor.mjs
node test_construction.mjs
```

Result: syntax checks pass; behavior regression exits 1. The `no_separator` case expected two `routine` observations and `repeated_branch_preserves_pair_alias=true`, but candidate output contained an empty observation list. Formal A01 remains `FAIL_AUDIT_CONTRACT_INVALID`; no source or old outcome was edited to make this test green. Candidate invocations after the formal run: 0; auditor invocations after the formal run: 0. A corrected candidate/oracle and allocation require a separate fresh freeze.
