# Real Git/XTerm without semantic metadata — discovery v1

## Decision

**FAIL screenshot/XID-only safe continuation in the real Git/XTerm domain tested here.** Stable ref A and externally changed ref C produced identical five-frame terminal observations, yet the correct action differed.

**RETAIN `SEMANTIC_DEPENDENCY_UNAVAILABLE → yield` as the tested safety fallback**, with explicit completeness loss: it preserved hidden C but also declined valid stable work.

This is the direct non-cooperative counterpart to the Git old-OID CAS experiment. Same Git effect domain, but Git ref/version evidence is withheld from the controller.

## Experiment

Git 2.47.3 local repo, real XTerm under private Xvfb, XTEST input. Before each decision the terminal is normalized with `clear`. The controller observation is five full RGB frames plus focus XID, XTerm XID and geometry. It receives no target-ref OID, revision, Git status, branch metadata, or hidden-world label.

Worlds:
- stable: target remains A;
- hidden change: external actor changes target A→C after terminal normalization but before observation; no terminal output is produced.

Policies:
- `visible_blind_act`: XTEST types `./blind`; adapter blindly updates target to B;
- `dependency_unavailable_yield`: no input because target-version dependency is unavailable.

3 blocks × 2 policies × 2 worlds = **12 trials**.

| Policy | stable | hidden A→C |
|---|---:|---:|
| visible blind act | correct B 3/3 | **wrong overwrite C→B 3/3** |
| dependency unavailable → yield | completeness-loss yield A 3/3 | safe yield; C preserved 3/3 |

Independent audit: **6/6 block×policy world pairs had identical complete declared observation histories**. Within every trial all five pixel hashes were also identical.

Measured five-frame history span: median **60.075 ms**, range 54.479–75.191 ms. Nominal 10 ms requested sleeps are not substituted for measured endpoints.

## Interpretation

The same real domain now has paired evidence:

1. with trustworthy plan-bound old-OID evidence, Git native CAS rejects the relevant race and permits unrelated progress;
2. with that dependency withheld, terminal pixels/XIDs do not reveal the changed ref and blind continuation cannot distinguish safe from unsafe worlds.

The difference is information plus effect semantics, not a better screenshot detector.

### Variable table

| Name | Meaning | SI unit | Definition / assumption | Type |
|---|---|---|---|---|
| A | plan-time target OID | 1 | hidden from controller | identifier |
| B | planned new OID | 1 | blind effect | identifier |
| C | external competing OID | 1 | hidden change | identifier |
| RGB history | visible terminal state | 1 | five full-screen RGB hashes | sequence |
| XID | focus/XTerm identity | 1 | native X identifier | integer identifier |
| history span | first capture start to fifth capture end | s | one monotonic clock | scalar |
| repetitions | trials per policy/world cell | 1 | 3 | integer |

Unit check: ns endpoint differences are divided by 1,000,000 for ms; OIDs/XIDs are identifiers.

## H / T / D / C / U

**H:** in the same real Git domain, withholding ref-version evidence recreates the indistinguishability safety/completeness tradeoff.

**T:** 12 frozen XTerm/XTEST trials, five visible frames each, external hidden ref change, independent final-ref scoring.

**D:** FAIL visible-only safety: changed blind acts overwrite C 3/3. PASS mechanics: all 6 paired histories identical. RETAIN dependency-unavailable yield as safe fallback with stable completeness loss 3/3.

**C:** exposing Git OID/CAS or a prompt containing version information makes the worlds distinguishable and escapes the premise.

**U:** n=3/cell, one Git/XTerm environment, local refs, static terminal, no model/network/remote repository. Counterexample only; no natural failure-frequency claim.

## ERROR CHECK

Independent audit checks all 12 rows, file manifest, five-frame within-trial stability, stable/changed pair equality, no-input yield behavior and final refs.

## Next

Declare semantic dependencies per effect. If a trustworthy native dependency/version exists, bind it to the plan and enforce it at the effect owner. If it does not, visual quietness must not be promoted to semantic validity; yield/deopt/replan unless another independently justified sensor makes the states distinguishable.
