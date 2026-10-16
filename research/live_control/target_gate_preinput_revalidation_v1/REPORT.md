# Target gate pre-input revalidation v1

Issue: #972  
Publication base: `592427d8f70efafed5819acec123f3fd0efa485b`  
Decision: **`PASS_PREINPUT_PATCH_REVALIDATION_SCOPED`**

## First outcome

One source-first frozen 2x2 block ran exactly once: four repetitions of each state/policy combination = 16 fresh private Xvfb+Tk sessions, reruns/replacements/tuning 0.

| State | Policy | Outcome |
| --- | --- | --- |
| stable | no revalidation | task-target clicked 4/4 |
| swap | no revalidation | predecessor failure reproduced: decoy clicked 4/4 |
| stable | one pre-input revalidation | `CURRENT_TARGET`, task-target clicked 4/4 |
| swap | one pre-input revalidation | patch error 240, `STALE_TARGET`, zero task clicks 4/4 |

All initial gates were eligible and every session ended with Button1 up. The candidate changes only one mechanism: one current screenshot immediately before pointer input, followed by the same radius5 / 11x11 / max-RGB-error<=8 patch comparison against the already gated patch.

The added capture took median **1.586 ms** [1.124, 3.864] on this container. In stable candidate cases, revalidation completion to click start was still median **5.192 ms** [5.098, 10.312]. These timings are descriptive only. They show that this repair closes the synchronized #965 mutation but does not create an atomic observation+input transaction; a smaller post-capture race remains possible.

## Interpretation

One pre-input current-patch revalidation is sufficient to close the exact temporal failure exposed by #965 without over-invalidating stable controls. This promotes a bounded **current-evidence revalidation component**, not patch equality as semantic identity.

The distinction with #956 remains critical: if a semantic substitution is pixel-identical, this patch revalidation cannot detect it. The candidate therefore addresses visible post-check staleness only.

## Integrity / scope

- source-first Git blob readback matched locally frozen PLAN/app/case/block/auditor bytes 5/5 before formal execution;
- formal invocation1, cases16/16, reruns0, audit errors `[]`;
- raw PNGs are container-only; Git retains compact per-case timing/disposition/effect records, source hashes and audit;
- private Linux/X11/Tk fixture only; no shared runtime mutation, model, token, natural race rate, cross-backend or production atomicity claim.

A later integration decision should compose this check with ordinary InputOwner/Executor authority only if the extra current observation is justified by measured task risk/cost. Do not promote it into an unconditional semantic-identity oracle.
