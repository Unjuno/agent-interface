# Persistent geometric world state R0 — plan

Parent #1526; task `PERSISTENT-GEOMETRIC-WORLD-STATE-R0-20260918-001`.

## Scope
Representation/currentness prerequisite only. External state must survive context compaction without promoting historical or inferred geometry to current action evidence.

## H/T/D/C/U
H: provenance role + source epoch + generation are necessary to distinguish current observed geometry from stale/inferred/unknown state after compaction and ABA-like generation changes.

T: standard-library Python typed store vs latest-geometry-only discriminator, independently structured history oracle; directed construction then one 200,000-trace frozen corpus, seed 152620260918001.

D: candidate/oracle mismatch0; candidate stale/inferred/unknown current promotions0; compaction semantic changes0; fresh re-observation accepted; ABA/compact/occlusion/inference stress each >=40,000; baseline false-current >0; audit/corruption/source integrity pass.

C: baseline is deliberately weak; PASS establishes a safety semantic requirement only. It does not show model/world-model/task benefit.

U: synthetic 2D boxes only; no GUI/model/token/latency/3D/product claim.
