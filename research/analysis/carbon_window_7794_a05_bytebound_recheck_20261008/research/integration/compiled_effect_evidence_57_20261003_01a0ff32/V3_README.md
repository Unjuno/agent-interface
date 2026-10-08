# Version 3: literal retained-raw graph prefix

This additive correction addresses nonauthor #6900 feedback [5964840413](https://github.com/Unjuno/agent-interface/pull/6900#issuecomment-5964840413) and [5964861115](https://github.com/Unjuno/agent-interface/pull/6900#issuecomment-5964861115). Actual author worker/session `01a0ff32-f520-79d2-b8cd-110e05130103`, FINAL-v5. It changes the evidence oracle, not production runtime behavior or original rows.

## Gap and correction

Version 2 checked terminal counts, release flags and mirrored critical events. Changing both copies of a terminal to `delivery_uncertain`, `failed` or the wrong action could still pass. Thus the original README's broad reachability/prefix description was not fully supported by version 2. Matching mirrors do not independently establish a valid history.

`test_audit_v3.py --legacy` first reproduced **30 accepted corruptions** among **32** changed raw copies (16 mutations in each arm); the numeric release alias was already refused in both arms. The fixed mutation deck preceded implementation. `audit_v3.py` keeps version 2's reference/type/source checks and independently builds literal expected events, adapter requests, completed transitions and pending effects from the declared finite two-step graph. It binds completed terminals to ordered `enter`/`save`, exact string action IDs, Boolean release flags, one-use authorization, exact integer sequences and the method-clipped `10000000` nanosecond deadline. Expected critical history derives from that literal graph, not agreement between recorded mirrors. All 32 corruptions now refuse. Tests also cover wrong operation, authorization, deadline, observation state, branch/effect action and verifier request.

All **72 baseline + 72 repaired retained rows** reconcile. The original baseline still has **18** successful-reference violations; the repaired arm still has **zero**. Three audit test methods pass normally and under Python `-O`. First RED and the separate output-path setup failure are retained under `checks-v3/`. The latter failed to write its result because an output path had too many parent components; the corrected raw-only command succeeded. No candidate graph/source arm, archive build or formal allocation was rerun.

## Custody and limits

Every previously published artifact remains byte-identical to head `b143e07779b3e00fd604858a3a9bcd2590c994de`, including v1/v2 auditors, all raw, README, old manifests and command failures. `V3_MANIFEST.json` binds the additions and the preserved old manifest; `V3_PUBLICATION.json` maps private/public path and newline/JSON formatting projections. Original private receipts/streams remain untouched; receipt stream hashes identify those originals. The first v3 staged whitespace check detected a unittest progress line's trailing space; a namespace-local attribute exempts immutable v3 command logs from whitespace lint, following the existing package's log treatment. No scientific field or raw record was changed to pass lint.

This literal checker covers the declared finite deck and graph prefix. It is not raw authentication, arbitrary graph verification, physical release evidence, adapter trust, live/backend behavior or an independent task-effect measurement. Reference syntax and valid graph ordering remain separate from effect authenticity. Version 3 imports only the old raw auditor and standard library; it never imports/executes runtime source or the producer. All additions stay under the manually used research evidence namespace; distribution and runtime test entry points remain unchanged.

Recheck existing raw from this directory with a fresh output:

```sh
python -B audit_v3.py before.json after.json <new-output>.json
python -B -m unittest -v test_audit test_audit_v3
python -B -O -m unittest -v test_audit test_audit_v3
```

The delivery head/proposal changes and needs fresh prospective content review. Previous-head votes and current-base confirmations do not automatically apply. Current-main combination and applicable platform requirements are separate gates; no main write is part of this correction.
