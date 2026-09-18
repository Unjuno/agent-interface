# A2 mixed-app guarded recovery — retained formal result

Issue #1728. Successor to #1711 setup stop and #1705 fixture PASS.

## Decision

**PASS_MULTI_APP_GUARDED_RECOVERY_A2_SCOPED**

One exact-frozen formal invocation ran four fresh private-X11 sessions. Every session exercised the same four stale-dependency refusals and four recovery task effects under one Chromium+XTerm lineage.

## Formal result

Formal discipline: formal1 / reruns0 / replacements0 / tuning0.

All 4/4 sessions:
- refusal order exactly `REFUSE_GEOMETRY → REFUSE_FOCUS → REFUSE_BINDING → REFUSE_OBSERVATION`;
- task-input counter unchanged across every stale refusal (16/16 refusal gates);
- four fallback task-input batches, each with intended Chromium window active immediately before input (16/16);
- exact independently observed effects `Downloads → History → Downloads → History` (16/16);
- replacement Chromium X ID differed from the old ID and the old window was absent before rebind (4/4);
- terminal keyboard/pointer neutral (4/4).

Environment: Python 3.13.5; Chromium 144.0.7559.96 on Debian 13; XTerm(398); Linux 6.18.44; private Xvfb/Openbox.

Independent audit PASS/errors[]. Corruption controls 7/7 rejected stale-input, wrong-active, wrong-effect, replacement, neutral-state, invocation-count and decision mutations.

## Integrity

Exact source was published before formal and remote Git blob readback matched local frozen bytes. A preformal byte mismatch was only one local-only comment in `common.py`; local bytes were corrected to the already-published remote source before formal, with no semantic code change.

Postformal source rehash matches every entry in `FREEZE.json`.

- RESULT SHA-256: `9fbc5ab7aa2efcc885b92a17f0702fa71aec3bd2478ca6d956c2b7c4577fda17`
- RESULT Git blob: `b0f46c531e168bd67fcfc70889c64e3833eedb0e`
- AUDIT SHA-256: `9662b3f8591ac1dc31a00b06f593ca714c73271ca63a6b820674913a4083e6de`
- AUDIT Git blob: `57c9ed9c30c00287d7857acf29422d1c91eb122a`

## Construction history

#1711 stopped before scientific task input because managed Chromium policy blocks the required local-file task effect. In #1728, a first integrated construction stopped before a complete row because Xlib `SetInputFocus` alone did not restore Chromium's WM-active state after XTerm focus drift. Construction-only recovery activation was strengthened with `wmctrl -ia`, an explicit primitive already allowed by #1711. The first complete construction then passed and is excluded from formal evidence.

## Interpretation

This closes the finite integration gap exposed by #1705 for this narrow environment: stale geometry, focus, binding and current-observation dependencies can all refuse before task input, and explicit refresh/rebind can recover to a correct independently observed effect on the intended Chromium top-level without leaving stuck input.

The result does **not** show that geometry-aware pointer routes are faster, that arbitrary browser tasks recover, that a model needs fewer boundaries, or that arbitrary long sessions are reliable. Built-in Downloads/History transitions are intentionally deterministic policy-independent task effects.

## Next rung

The ROADMAP's broad longer-session claim still requires duration/variety beyond four finite transitions. A useful next discriminator should preserve these refusal/recovery gates while adding repeated cycles or a second independently scored task family; do not weaken the zero-input-on-stale rule.
