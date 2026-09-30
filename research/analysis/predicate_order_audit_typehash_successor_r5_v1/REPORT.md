# Predicate-order auditor type/hash boundary — allocation 05

Issue #5018 successor allocation 05. Preserve predecessor allocations 01–04, including allocation 04's runner PASS and read-only audit STOP; no result is pooled or rewritten.

## H / T / D / C / U

**H.** On the exact unchanged 336-row, 21-distribution raw corpus, the retained auditor accepts each of seven preregistered Python bool/int equality mutations while the exact recursive type-shape candidate rejects them. An independent raw-only audit then binds runner result to the raw bytes, and a separate exact-path manifest verifier accepts all declared digests while rejecting empty maps, omitted paths, and changed digest.

**T.** Allocation `predicate-order-typehash-20260928-05`; dedicated branch `research/predicate-order-audit-typehash-successor-r5-20260928`; additive path `research/analysis/predicate_order_audit_typehash_successor_r5_v1/`. One pinned offline Docker Desktop linux/amd64 container runs tests, syntax, baseline probe, formal runner, independent audit, and manifest verification in sequence. `/out`, `/repo/out`, `/evidence`, and `/audit` are aliases of the same fresh writable directory; `/src` and `/repo/src` alias read-only source; `/input` and `/repo/input` alias read-only frozen input. No retries.

**D.** PASS only if all frozen stages complete with exact raw hash/size, 336/21 baseline, all seven auditor acceptances and candidate rejections, zero independent-audit errors, complete positive exact-path manifest, and rejection of all three negative controls. Otherwise preserve typed FAIL/HOLD/STOP; no rerun or post-result gate changes.

**C.** Same retained auditor, candidate, raw bytes, pinned image, declared canary set, and offline resource limits. Allocation 04 is not pooled. The path aliases specifically repair its audit-output permission boundary. One synthetic corpus and one host only.

**U.** No general security or JSON interoperability claim, new predicate-order science, performance claim, GUI/task effect, GPU, provider, or production authority.

## Formal result

`PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED` in the single frozen Docker allocation; container exit 0. All four unit tests passed, Python AST and shell syntax passed, and the excluded baseline construction probe reconstructed 336 rows / 21 distributions. That excluded probe accepted six of seven listed mutations; its separate replay-cost mutation was rejected by replay consistency and was not pooled into the formal denominator.

The formal unchanged raw input matched SHA-256 `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`, 186,739 bytes. Baseline was 336/336 rows, 21 distributions, errors empty. Each of the seven frozen canaries was accepted by the retained auditor and rejected by the strict candidate. Independent audit: `PASS_RAW_AUDIT`, errors empty, seven candidate rejections. Manifest: `PASS_MANIFEST_BINDING_SCOPED`, exact positive map bound 11 source files and four input/output paths; empty maps, omitted path, and changed digest all rejected.

The Docker invocation aliased `/out`, `/repo/out`, `/evidence`, and `/audit` to the same fresh writable directory while keeping the two source and input aliases read-only. This resolved allocation 04's read-only audit-output failure without changing gates after execution. All 26 frozen output artifacts and their SHA-256 digests are recorded in `RESULT.json` and committed verbatim under `result/`. No retries or post-result gate changes occurred.

## Limits

One retained synthetic corpus and one pinned Linux/amd64 Docker Desktop host. This supports only the bounded type/binding audit hypothesis; no broad security/JSON interoperability, new predicate-order science, performance, GUI/task effect, provider, GPU, or production claim.
