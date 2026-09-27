# Predicate-order auditor type/hash boundary — allocation 05

Issue #5018 successor allocation 05. Preserve predecessor allocations 01–04, including allocation 04's runner PASS and read-only audit STOP; no result is pooled or rewritten.

## H / T / D / C / U

**H.** On the exact unchanged 336-row, 21-distribution raw corpus, the retained auditor accepts each of seven preregistered Python bool/int equality mutations while the exact recursive type-shape candidate rejects them. An independent raw-only audit then binds runner result to the raw bytes, and a separate exact-path manifest verifier accepts all declared digests while rejecting empty maps, omitted paths, and changed digest.

**T.** Allocation `predicate-order-typehash-20260928-05`; dedicated branch `research/predicate-order-audit-typehash-successor-r5-20260928`; additive path `research/analysis/predicate_order_audit_typehash_successor_r5_v1/`. One pinned offline Docker Desktop linux/amd64 container runs tests, syntax, baseline probe, formal runner, independent audit, and manifest verification in sequence. `/out`, `/repo/out`, `/evidence`, and `/audit` are aliases of the same fresh writable directory; `/src` and `/repo/src` alias read-only source; `/input` and `/repo/input` alias read-only frozen input. No retries.

**D.** PASS only if all frozen stages complete with exact raw hash/size, 336/21 baseline, all seven auditor acceptances and candidate rejections, zero independent-audit errors, complete positive exact-path manifest, and rejection of all three negative controls. Otherwise preserve typed FAIL/HOLD/STOP; no rerun or post-result gate changes.

**C.** Same retained auditor, candidate, raw bytes, pinned image, declared canary set, and offline resource limits. Allocation 04 is not pooled. The path aliases specifically repair its audit-output permission boundary. One synthetic corpus and one host only.

**U.** No general security or JSON interoperability claim, new predicate-order science, performance claim, GUI/task effect, GPU, provider, or production authority.

## Status

Pre-registration only. Formal allocation has not run. See `FREEZE.json` for exact source/input identities and execution limits. Results and all logs will be appended after the single run.
