# Retained #4036 keyboard activation experiment

Read REPORT.md first. Result: PASS_FOCUS_ACTIVATION_RECIPE_BOUNDARY_SCOPED, not production acceptance. An ordinary click repaired a pre-activation internal Tk focus change; exact native-child X focus alone did not. All routes remained vulnerable to the declared later focus change. The scoped counterexamples and negative outcomes are retained.

FREEZE.json and PREFORMAL.md were committed before formal input. Full source, all raw binary images/JSONL/request/response/process exits, construction failures and unchanged auditor are preserved in the nine parts of one XZ/TAR capsule. CAPSULE.json binds each part, the full archive, expanded tar,367 member files and12241141 original bytes. The parts are not individually valid XZ files: concatenate only in manifest order. No historical run should be rerun.

Safe read-only reproduction (new destination required):

```sh
python -B unpack.py /tmp/activation-4036-review
python -B /tmp/activation-4036-review/audit.py /tmp/activation-4036-review
cd /tmp/activation-4036-review
python -B -m unittest -v test_audit
```

Expected formal audit:30 cases,12 correct A,15 wrong B,3 no-input; errors empty. Thirteen test methods pass, including12 semantic corruption variants. These repeat offline verification only. The unpacker performs bounded integrity checks, permits only regular relative members and refuses an existing destination; it never imports/executes archived source. Hashes are integrity checks, not authentication.

run.py is also supplied as directly readable exact frozen source. Backend code is byte-identical to current-main blob9cae101a219348077668c8fc086acf8e13154afe; the archived loader omits only its unused manifest import. No shared runtime, public CLI/MCP, core admission, model, token/latency benefit, general GUI guarantee or completed roadmap is claimed. Actual environment is the supplied Linux x86_64 container, not a Docker/OrbStack image-attested replication.

The previous 266-file focus ZIP remains conversation-hosted and unchanged; only its identity and the relationship are recorded here, not a claim that all predecessor data has been uploaded. Same-author separate raw auditor is not an independent human review. Repository-wide CI and merge/readback must be evaluated on the actual PR head.
