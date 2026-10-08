# Activation recovery: pointer hit target and keyboard recipient are separate

**Result: PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED.** This is a finite boundary finding, NOT approval of an unconditionally safe recovery recipe.

Allocation `activation-hit-target-20260922-01` completed all 26 fresh Tk cases in three predeclared batches of 9/9/8. Formal batch invocations: 3; reruns/replacements/exclusions: 0. All 26 application exits and all three server/runner exits were observed as zero. The separate raw-only auditor passed 3,094 checks with zero errors; all 12 copied-evidence controls rejected; seven policy unit tests passed. These are independent implementations/processes by the same author, not external human review or another-machine replication.

## Main result

Each ordinary recipe has eight cases: two repetitions of clear, cover-before-check, cover-after-check, and unrelated-cover schedules. Two additional no-task-input controls retain common focus/motion but no click or key.

| Recipe | Correct A text | Wrong B text | Unwanted cover callback | Cases |
|---|---:|---:|---:|---:|
| CLICK_THEN_TYPE | 4 | 4 | 4 | 8 |
| POST_FOCUS | 4 | 0 | 4 | 8 |
| HIT_AND_FOCUS | 4 | 0 | 2 | 8 |
| NO_TASK_INPUT | 0 | 0 | 0 | 2 |

All three recipes preserved both clear and unrelated-cover positives: target A became `7`, B stayed empty, and the counter stayed zero. The two controls remained blank.

With a cover already present at the hit check, CLICK_THEN_TYPE clicked the ordinary Button and typed into B; POST_FOCUS prevented the B text but retained that Button effect; HIT_AND_FOCUS refused before button-down and preserved both entries/counter. With the cover introduced AFTER the hit check, all three recipes clicked the Button. The two recipient-checking recipes still prevented the wrong text, but neither undid or prevented the callback.

The target Entry retained its exact native XID and root geometry throughout. The separate X connection's pointer-child walk and Tk's independent containing-window query agreed. All terminal native keymaps/buttons were neutral. Neither unchanged geometry nor successful release established the absence of a collateral application effect.

## Conditional argument

The clear and covered observations agree on target identity and geometry but disagree on the actual pointer hit child and resulting Button callback. Thus target identity/geometry alone is insufficient for this recovery choice in the observed fixture. A post-click recipient check occurs after an ordinary Button can commit its callback; refusing the later key does not roll back that prior effect. A before-click hit check works only for the tested states stable between that observation and click. COVER_AFTER is the explicit remaining counterexample, not a failed case removed to improve the result.

The documentation's distinction is consistent with the observation: Tk's `winfo containing` selects the highest stacked sibling at a point, while `winfo viewable` only establishes that the widget and its ancestors are mapped. The live implementation evidence is on Tk 8.6.16; the consulted online manual is 8.6.18. The retained installed class bindings and native traces, not an assumption of version equality, ground this allocation.

## Exact scope and sources

- Source intake main: `2308b8301d69b7089a2e0636486736ed59b61537`.
- Closing read of main: `33e86e997d02b769af17a3f03f6035c68927da6e`; the new namespace returned 404 there. This is a bounded noncollision check, not knowledge of unpushed work.
- Full unchanged backend Git blob: `9cae101a219348077668c8fc086acf8e13154afe`; SHA256 `3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8`.
- Local preformal source commit: `28cd462abb4380ed93d2484be9202cf26aad7f97`. This is an isolated local Git root, NOT a descendant of upstream main and NOT published.
- Local freeze SHA256: `038ed3ad71ac52e5adf83433440fb7818bc3db9ce61de5e6a1dfe059ef7c7a1e`.
- Original formal AUDIT.json SHA256: `4fec833d445258dea5d4c84f60034001661230312b63c9f09a804e045d0bd52a`.

The loader omits one unused core-manifest import; all backend method bodies remain exact. Direct backend focus, geometry, pointer and key methods are exercised. Public CLI/MCP, core admission, the full execute path, leases, automatic semantic target discovery, and real model decision-making are not exercised. Do not promote this as an integrated desktop PASS.

Provided Linux x86_64 execution container, CPython 3.13.5, Tcl/Tk 8.6.16, Python-Xlib 0.15, private authenticated TCP-disabled Xvfb 640x360x24. Docker/OrbStack image attestation is unavailable here, not globally unavailable. No installation, model/provider, external experiment network, host desktop, clipboard, or user documents. No performance or token benefit was measured.

## Retained engineering failures

CONSTRUCTION.zip preserves all four excluded construction invocations and prior source versions. Construction 01 stopped before any click or key because old Python-Xlib did not use the initial wildcard Xauthority entry; the Tk application itself connected. Server and app termination evidence is retained. Construction 02 passed one clear smoke case after adding an exact local-family entry for the same generated cookie. Construction 03 passed the 12-cell matrix. Construction 04 repeated that excluded matrix with opaque session IDs and raw stdin/stdout retention, then passed the raw audit and 12 mutation controls. None of these cases contributes to the formal denominator. The initial public-source direct download failed at DNS (curl exit 6); source was obtained with GitHub MCP and manually materialized with exact whole-blob verification.

No old formal result was edited, rerun or replaced. The previous conversation's scheduler bundles remain unchanged and are not inputs to this GUI experiment. Their original SHA256 identities are retained in INTAKE.json and checked at delivery.

## Integration decision and remaining unknowns

Reject `click succeeded -> intended recipient restored without collateral effect` as an unconditional caller rule. A post-click recipient gate protects subsequent keyboard routing only. A native hit check adds useful before-click evidence but does not provide atomicity. Keep the two observations, actual button/key emissions, release, and application effects separate in the caller's result vocabulary.

The component handoff to #55/#57/#2789 is a bounded support constraint for the click recipe investigated in #4036. It does not authorize moving/removing the cover, blind retyping, Undo, or automatic retry. Cooperative same-app native siblings and a stable fixture between declared barriers are important assumptions. Foreign overlays, grabs, missing focus APIs, disabled/populated targets, IME, selection, concurrent changes after the final focus check, arbitrary toolkits, and model usefulness remain unknown. No population reliability estimate, calibrated combined timing uncertainty, or production default follows.

## Delivery

`STOP_PUBLICATION_NO_WRITE_CAPABILITY`: the current GitHub connector exposes read operations only; directory search found only the already installed GitHub connector, and this environment has no authenticated gh/token route. No remote Issue, branch, PR, merge or deletion was performed. ISSUE_PROPOSAL.md and PR_DRAFT.md are unposted delivery drafts. Source and gates were frozen locally, not publicly preregistered. Preserve that chronology on any later publication.

Readable source, all first raw outcomes, native image bytes, construction failures, exact process receipts, independent checker and copied-evidence controls are included. Packaging and restoration are read-only validation, not formal reruns. The global ROADMAP and all broader acceptance boundaries remain open.

## Primary references

- https://github.com/Unjuno/agent-interface/issues/55
- https://github.com/Unjuno/agent-interface/issues/4036
- https://github.com/Unjuno/agent-interface/pull/4053
- https://github.com/Unjuno/agent-interface/issues/2789
- https://github.com/Unjuno/agent-interface/blob/2308b8301d69b7089a2e0636486736ed59b61537/runtime/backends/x11_v1/backend.py
- https://www.tcl-lang.org/man/tcl8.6/TkCmd/winfo.htm
