# Post-hoc byte-binding audit v2

## H — hypothesis

The retained v1 auditor computes SHA-256 values for `raw.json` and `audit.json`, but does not compare those bytes with the expected digests in `BINDING.json`. A byte-only mutation such as appending a newline can therefore leave the parsed rows unchanged and still receive the v1 semantic PASS.

## T — verification

Preserve all v1 evidence and source unchanged. Execute the exact retained auditor source from commit `cfbc49f9711bd49a6a60a138daa656009256017f` against the frozen `raw.json`, `audit.json`, `BINDING.json`, and `INDEPENDENT_AUDIT.json`. The v2 wrapper first enforces byte hashes from the binding, then reproduces the v1 report and its six semantic mutation controls. Two additional controls append one LF to either raw or audit bytes and require rejection before JSON parsing. On the exact retained bytes, the v1 semantic auditor was also run on both newline-mutated payloads: each hash changed, yet each still returned `PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED`. This reproduces the review finding without rerunning the workflow.

Local validation: Python 3.14.5; `python3 -m unittest -v test_independent_audit_v2.py` (4/4); `python3 -m py_compile independent_audit_v2.py test_independent_audit_v2.py`; exact frozen-artifact reproduction recorded in `INDEPENDENT_AUDIT_V2.json`. The CLI accepts explicit `--raw`, `--audit`, `--binding`, `--expected-report`, `--legacy-auditor`, and `--out` paths; it never modifies the historical inputs.

## D — decision

`PASS_BYTE_BOUND_RAW_ONLY_REPRODUCTION`: 90 rows / 90 unique identities, raw and audit SHA-256 match the frozen binding, all six legacy semantic corruption controls reject, both byte-only newline mutations reject under v2, and the v1 report is reproduced byte-for-byte. The v1 false-pass on both newline mutations is reproduced and retained as a finding. The original v1 report and auditor remain unchanged.

## C — controls

The v2 wrapper is additive and hash-binds bytes before decoding. It uses the exact v1 auditor and frozen inputs; no row, decision, or historical report is rewritten. The regression tests include matching bytes, raw newline mutation, audit newline mutation, and missing binding digests.

## U — limits

This is a local post-hoc audit-code hardening check over one retained artifact. It is not a new workflow, Docker/Xvfb replication, formal task run, model evaluation, runtime change, latency measurement, or product claim.
