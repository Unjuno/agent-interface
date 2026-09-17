# OpenTTD guarded framed macro transfer — retained first outcome

Task `OPENTTD-GUARDED-FRAMED-MACRO-TRANSFER-20260917-001`, Issue #914.

## Disposition

**`PASS_OPENTTD_GUARDED_MACRO_TRANSFER_SCOPED`**.

One source-first frozen deterministic formal invocation produced 10 rows = 5 retained states x 2 representations. Formal reruns/replacements/tuning: 0. No OpenTTD, GUI, model, provider, network, task input, or shared-runtime mutation occurred during measurement.

## Frozen input identities

- source procedure Git blob `6994af75e1873c967a6f300e727ebd71058952cb`;
- retained 1280 report blob `8ba7a6dab708491c4e4f523f95b8d49f634560e5`;
- retained 1152 report blob `f954652d5ff71c20815221a40bcc1e9dc554c798`;
- retained binding-fault report blob `10e1e0219d5340094a0e1f628ea720a3c0c29130`.

Source-first local `FREEZE.json` SHA-256: `a24cad5abf85a52d62ef1eb036c493147db5f8755b233ba407b6cd5bd44d9775`.

## First outcome

- guarded candidate exact current FIRST+CONTINUATION path: **4/4** ordinary states;
- guarded candidate exact retained branch semantics: **4/4** (`met -> CONTINUE`, `target_not_reached -> YIELD_TARGET_NOT_REACHED`);
- literal raw replay window-content path mismatch: **4/4** changed-resolution states;
- screen-chrome representation unchanged in every row;
- binding-fault candidate: **`YIELD_BINDING_CHANGED`**, emitted pointer target `null`, matching retained zero pointer admissions;
- authority `none`: **10/10**; task-input call `false`: **10/10**.

The literal arm is a representation-only counterfactual. It is **not** a claim that the historical system executed those raw coordinates or failed the task.

## Integrity

- formal rows SHA-256 `f5df6efd78ad716e57d8a66636055fa03ff16a50bedc42b119e23f69f750712f`;
- result SHA-256 `8b818f198d82ffa97c3daa8608fc9cd0b6bcead06c38b891209744c25aa5ae39`;
- independent audit SHA-256 `93bda04512c6313d8cb9c80dcc25aa2c79b01f4b76f1cbdba1cf6eee980cf0a5`, errors `[]`;
- postformal frozen-source hashes exactly match the premeasurement freeze;
- copied-evidence corruption controls reject **5/5**: candidate path +1, branch escape, authority escalation, binding-fault pointer escape, and false literal historical-failure claim.

`SOURCE_BUNDLE.json.gz.b64` is a deterministic gzip(mtime=0)+base64 wrapper around the exact source bundle; decoded JSON SHA-256 is `757a028f0a2ef2dd54844c0bc523f0666ab6728646d3beb985a397b7b10694ea`. `EVIDENCE.json.gz.b64` similarly wraps the exact formal/result/audit/control bundle; decoded JSON SHA-256 is `1477571eedee87eff43de2ed2eee0842bbb5813f458ecad20b356620af52fdd2`. `reconstruct.py` verifies both decoded identities before extracting frozen sources/evidence.

## Interpretation boundary

This transfers the guarded-macro representation principle from the retained Chromium handle experiment to one retained OpenTTD mixed-coordinate-frame procedure. The useful property is not the literal coordinates: it is preserving authored frame roles plus a current binding dependency so window-content paths are resolved against current geometry while screen-fixed chrome remains fixed, and refusing after binding drift.

This does **not** establish automatic coordinate-frame discovery, arbitrary procedure compilation, a new live OpenTTD task outcome, latency/token benefit, or production ABI promotion.
