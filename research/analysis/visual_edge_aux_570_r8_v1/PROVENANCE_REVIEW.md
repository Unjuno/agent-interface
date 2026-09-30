# Post-run provenance review — Issue #4885 R8

This note supplements, and does not edit, the pre-inference `FREEZE.json`, runner, inputs, raw calls, or audit.

## Discrepancy

`FREEZE.json` records `base_main=cd7853030248c0d19293bf573cd7c90109b1a57e`. Git history shows the owned branch was actually created at `1ffefc0ac3facd396fe1d930896c8c548c5522b1`; that commit's parent is `cd7853030248c0d19293bf573cd7c90109b1a57e`. Therefore the frozen field is an ancestor of the branch's direct starting point, not its exact branch base.

The source/input freeze commit `6e7d8a055eec5dfb60baeae13d7e9ff9c7c10b34` descends from `1ffefc0`. The formal evidence commit `af067519c7d0a9689e740373ae8ac0932b1ff2a2` descends from the source/input commit. The exact pre-inference main recheck was `055468a4831960f5647760d4f25c54923526c5a3`, whose parent is `1ffefc0`; this exact recheck is correctly recorded in the freeze. A GitHub compare from the recorded ancestor `cd7853` to pre-inference main `055468a` showed only broker-path-confinement #4876 and Needle support-replication #4884 additions, both outside this experiment path.

## Effect on disposition

The branch-root metadata discrepancy is a provenance limitation and is retained as such; it does not change any frozen source, input, prompt, model, raw response, or metric. All 38 pre-inference GitHub readbacks matched, and the current-main recheck was disjoint. The formal disposition remains `HOLD_AUDIT_OR_GPU` due the two frozen response-schema errors for absent-target EDGE rows; no scientific PASS/FAIL/REJECT conclusion is issued. No rerun or retroactive freeze edit is made.
