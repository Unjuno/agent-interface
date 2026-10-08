# Issue #7707 — complete source-manifest coverage before MUS diagnosis

## H / T / D / C / U

**H.** Binding each listed clause to exact bytes is insufficient if an actual source line can be omitted or two clauses can alias the same identity. Requiring exactly one complete span per nonempty physical source line, with unique clause IDs, before solving will detect these manifest-completeness defects.

**T.** Freeze against current `main` and run ten deterministic byte-exact cases: SAT, pair conflict, two independent MUSes, omitted source clause, duplicate span, duplicate clause ID, partial span, Unicode-prefix byte offsets, declared unknown syntax, and CRLF line endings. Run candidate once, then an independent byte/line/assignment auditor once in WSLc using only a cached pinned Python image (`--pull never`, network none, read-only source, separate output). Six in-memory mutation controls; no retries.

**D.** `PASS_MANIFEST_COVERAGE_BOUNDARY` requires all ten independent oracle matches, complete one-to-one coverage of every nonempty physical line, unique IDs, fail-closed malformed manifests before SAT/MUS, explicit UNKNOWN for declared unparseable rows, exact complete minimal-core sets, no dispatch/input authority, and rejection of every mutation. A candidate/runtime/auditor failure is retained as FAIL/STOP with no retry.

**C.** The source grammar is intentionally line-oriented; complete coverage might be too strict for headings/comments/mixed prose. It cannot establish faithful semantic encoding.

**U.** Finite synthetic byte/line/Boolean method only; no natural-language fidelity, human explanation/comprehension, GUI/runtime authority, task effect, general solver performance, resource enforcement, or product-safety result. The prior #7501 T0/A01/A02 records remain immutable.

Issue #7707 is the successor to closed #7501. The precise gap is: A02 checked every supplied span but did not test that all source lines were represented. This is a separate coverage boundary, not an A02 rerun.
