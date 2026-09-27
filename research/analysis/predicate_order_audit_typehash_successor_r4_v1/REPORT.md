# Predicate-order audit type/hash boundary — allocation 04

Issue #5018. This is a new allocation after allocation-03's preserved `STOP_PROVENANCE_OR_RUNTIME`; that consumed allocation is not retried. The predecessor data, #4994, #5006, #5012, and PR history remain unchanged.

## H / T / D / C / U

**H.** The specified hardened auditor accepts Python JSON booleans in several numeric-looking fields because `True == 1` and `False == 0`. A strict JSON type-shape boundary should preserve the unchanged 336-row corpus while refusing each frozen bool/int substitution. A separate exact-path SHA-256 verifier should accept a complete source/output manifest and reject empty maps, an omitted path, and a changed digest.

**T.** Allocation `predicate-order-typehash-20260928-04`; branch `research/predicate-order-audit-typehash-successor-r4-20260928`; additive path `research/analysis/predicate_order_audit_typehash_successor_r4_v1/`. Input is the exact `RAW.json` recovered from archive blob `c38dd2002f201d49b6fc261caff019550a4bf4bc`, SHA-256 `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`. The exact retained auditor is Git blob `b314562f69633f2d4771d531ee747d7a856db2e4`. Candidate, runner, raw-only auditor, manifest verifier, tests, shell entrypoints, image digest, commands, output paths, canary cases, and gates are frozen in `FREEZE.json` before the only formal invocation.

The seven fixed mutations are `cost.A=True`, `drift_grid[0]=False`, final `alpha=True`, row-1 `state_id=True`, row-0 `truth.A=0`, row-0 `NAIVE.evaluations=True`, and row-0 `NAIVE.semantic_mismatches=False`. A separate runner compares the retained auditor with an exact recursive JSON-type-shape candidate. A raw-only auditor imports neither runner nor candidate and independently binds the input hash, row/distribution counts, canary paths/replacements/mutation hashes, and decisions. It writes an exact source/output digest map; a third fresh process validates the positive manifest and three negative controls.

Docker Desktop image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/amd64`), offline, read-only root and source, 0.25 CPU / 512 MiB / 64 PIDs. No model, GPU, provider, GUI, user data, package installation, or production runtime.

**D.** `PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED` requires the exact baseline, all seven baseline accepts and strict-candidate rejects, independent audit `errors=[]`, the complete positive exact-path manifest, and rejection of all three negative controls. Any miss remains a typed FAIL/HOLD/STOP; no retry or post-result gate changes.

**C.** One synthetic corpus and one Docker Desktop host. The candidate's recursive type-shape comparison uses the retained immutable raw document as the expected JSON type schema. This does not prove arbitrary schemas, package security, or general cross-version compatibility.

**U.** No new predicate-order scientific claim, broad audit/security guarantee, live GUI/task effect, performance, product, or production authority conclusion.

## Excluded construction record (not formal)

Before the freeze, a diagnostic run of the retained auditor reconstructed 336/336 rows and 21 distributions. Seven declared bool/int substitutions were accepted; a separate `NAIVE.cost=True` mutation was rejected by replay consistency. This diagnostic is construction only and is not pooled. A separate Docker unit run passed 4/4 tests; Python AST parsing and all three shell syntax checks passed. The formal, independent-audit, and manifest output directories were empty at freeze.
