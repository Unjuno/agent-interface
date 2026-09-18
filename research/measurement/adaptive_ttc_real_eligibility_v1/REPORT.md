# #1027 real adaptive-TTC eligibility audit v1

Snapshot main: `66a72f17518d7b978309b186662d017cebef5b6b`.

Decision: **`HOLD_NO_REAL_ADAPTIVE_RESIDUAL`**.

This is the Rung0 eligibility result allowed by Issue #1027. It does not train, run or benchmark an adaptive policy. It asks only whether the repository currently contains a legitimate real `NEEDS_POLICY` residual with enough leakage-free rows and an independent semantic/effect oracle to justify the frozen `FULL_DEPTH` versus `ADAPTIVE_TTC` shadow experiment.

## Exact retained evidence

- Cross-domain rule VM result blob `20ed6bc4c682e5d2e1cf60fb44f4fcdf5a1bd21d`: Chromium exact 8192/8192; retained OpenTTD exact 5/5; fail-closed controls pass. These rows do not supply a learned residual without semantic weakening.
- MAP01 v31 last-effect result blob `9b131cc22860ca210959202790688a0759bc8b24`: five eligible retained rows, enriched collision groups 0. The retained report explicitly says this does not establish population-level representation sufficiency and that a materially larger leakage-free corpus plus independent semantic/effect oracle remain required.
- #1026 retained comment `5720862825`: `BLOCKED_REAL_SHADOW_DATA`; deterministic Chromium/OpenTTD leaves no residual and the retained MAP01 cohort was too small.
- #1027 retained update `5730673024`: after #1511 representation repair, five rows still do not activate adaptive TTC; genuine real residual and independent oracle remain absent.
- #1223 remains a separately owned active upstream real-state census. Its unpublished/in-flight result is not consumed by this audit. The Git-retained reservation blob is `eaf2e5c01288e2531a1767ffd22731ee6d9bb646`.

## Six activation prerequisites

| prerequisite | current status |
|---|---|
| real caller-visible retained/shadow decision contract | yes |
| representation sufficiency for a frozen residual | **not established** |
| genuine `NEEDS_POLICY` residual after deterministic coverage | **not established** |
| enough leakage-free rows for frozen train/eval | **no** |
| independent semantic/effect oracle | **no** |
| first transfer rung has no live-input authority | yes |

Four prerequisites therefore fail. The result is a dependency/eligibility HOLD, not a capability failure.

## Container validation

The source-bound validator reproduced the HOLD with no integrity errors. Five corruption controls were all rejected as `FAIL_INTEGRITY`:

1. consuming unpublished #1223 result;
2. declaring the five retained MAP01 rows sufficient against their source boundary;
3. inventing an independent semantic/effect oracle;
4. relabeling deterministic-exact Chromium/OpenTTD rows as learned residuals;
5. using future/oracle evidence as a candidate feature.

The first control-suite attempt is retained separately as scientific `NONE`: it tried to build a positive control by mutating retained source facts from 5 to 64 rows, and the source-identity validator correctly rejected the test fixture itself. The repair changed only the test-control design, not H/T/D/C/U or source facts.

Independent audit does not import the validator and rechecks the source identities, deterministic closure, five-row boundary, active-upstream exclusion, four failed prerequisites and all corruption outcomes.

## H/T/D/C/U result

**H:** current retained evidence is insufficient to activate adaptive TTC. **Supported at this snapshot.**

**T:** retained-source matrix + disposable-container validation only; no training/model/GUI/X11/task input/provider call.

**D:** `HOLD_NO_REAL_ADAPTIVE_RESIDUAL`. Do not allocate `FULL_DEPTH` vs `ADAPTIVE_TTC` yet.

**C:** a later completed source-bound lane, including #1223 or another independently scored real decision family, may establish a genuine residual and enough rows. This HOLD must not be generalized into “adaptive computation is useless.”

**U:** snapshot-bound eligibility only. No classifier competence, adaptive speedup, safety, model-token, live-authority, or production claim.

## Next condition

Do not create a synthetic TTC substitute. Revisit only through a fresh successor after a completed, retained upstream result establishes all missing prerequisites: a genuine residual after deterministic coverage, a leakage-free corpus large enough for a frozen train/eval allocation, and an independent semantic/effect oracle.
