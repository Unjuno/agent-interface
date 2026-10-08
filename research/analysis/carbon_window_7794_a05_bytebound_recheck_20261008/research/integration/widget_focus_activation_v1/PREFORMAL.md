# Issue #4036 preformal gate

Formal state: 0/30. Freeze commit dfd747fdeed3bcd41df65520f649761e878a6a74; FREEZE.json SHA256 3468b572d0210edd2dff512473c592dc4ac68bc4a57b07299ec77c88b64953e8, read-back blob b42dc6bd7e79a7a4305608f80f377b91f1b21976. This commits source hashes and plan before execution; full source and raw delivery follow afterward.

Excluded construction: first ready timeout and second target-ancestry setup STOP retained; three-route and nine-condition construction subsequently completed. Thirteen offline tests pass, including twelve semantic corruption variants. Environment metadata lookup failed once and was corrected using the actual module version before freeze. These are local engineering records under #4036, not separate scientific successors.

Frozen exact table, three repetitions per cell. Payload is 7; other Entry remains empty.

| Route | Stable A | B before activation | B after activation |
|---|---|---|---|
| TOPLEVEL_FOCUS | A receives 7 | B receives 7 | B receives 7 |
| CHILD_XID_FOCUS | A receives 7 | B receives 7 | B receives 7 |
| CLICK_ENTRY | A receives 7 | A receives 7 | B receives 7 |

Three additional NO_INPUT controls remain blank. Aggregate expected: 12 correct A, 15 wrong B, 3 no input. All nine child activations must show exact A native XID at immediate readback; this does not substitute for the observed internal recipient. All nine clicks must reach A and restore internal focus A before any later scripted focus change.

PASS_FOCUS_ACTIVATION_RECIPE_BOUNDARY_SCOPED also requires complete thirty-case/source/event/command/effect/exit/cleanup/hash accounting and raw-only audit plus corruption controls. Top-level and child-only focus remain rejected recovery recipes for an already-focused B in this fixture. Click is scoped to current geometry and no subsequent focus change, never a general safety guarantee. Full evidence with unexpected semantics is scientific FAIL; incomplete/source/process evidence is STOP/HOLD.

Exactly three ten-case batches, route order rotated by batch. Each command is `/opt/pyvenv/bin/python -B /mnt/data/focus_successor/research/integration/widget_focus_activation_v1/execute_batch.py /mnt/data/focus_successor/research/integration/widget_focus_activation_v1/formal-01/batch-N --batch N` for N=0,1,2, once each and in order. Each requires prior complete batch and actual exit0. Inner process deadline38s; enclosing tool requested42s. No retry, replacement or pooling. Full PLAN.md is SHA-bound in FREEZE.json.

Only isolated native X11 input, no model/provider/network experiment, shared runtime changes, public CLI/MCP/core-admission or product claim. Provided execution container only; no Docker/OrbStack image-attested replication.
